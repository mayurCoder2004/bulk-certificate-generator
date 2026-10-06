from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import GenerationJob, Recipient
from app.main import app
from app.services.certificate_service import generate_certificate


TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_certificate_returns_pdf(client, db):
    job = GenerationJob(
        event_name="Python Workshop",
        certificate_title="Certificate of Completion",
        organization="Aereo Learning",
        event_date=date(2026, 10, 6),
        status="PROCESSING",
        total_recipients=1,
        completed_count=0,
        failed_count=0,
    )

    db.add(job)
    db.flush()

    recipient = Recipient(
        job_id=job.id,
        name="Mayur Pawar",
        email="mayur@example.com",
        status="PROCESSING",
    )

    db.add(recipient)
    db.commit()
    db.refresh(recipient)

    certificate_path = generate_certificate(
        job=job,
        recipient=recipient,
    )

    recipient.certificate_path = certificate_path
    recipient.status = "COMPLETED"
    db.commit()

    response = client.get(
        f"/api/certificates/{recipient.id}"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == f'attachment; filename="certificate_{recipient.id}.pdf"'
    )
    assert response.content.startswith(b"%PDF")


def test_get_certificate_returns_404_for_failed_recipient(
    client,
    db,
):
    job = GenerationJob(
        event_name="Python Workshop",
        certificate_title="Certificate of Completion",
        organization="Aereo Learning",
        event_date=date(2026, 10, 6),
        status="FAILED",
        total_recipients=1,
        completed_count=0,
        failed_count=1,
    )

    db.add(job)
    db.flush()

    recipient = Recipient(
        job_id=job.id,
        name="Failing User",
        email="failing@example.com",
        status="FAILED",
        error_message="Certificate generation failed",
    )

    db.add(recipient)
    db.commit()
    db.refresh(recipient)

    response = client.get(
        f"/api/certificates/{recipient.id}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate is not available"


def test_get_certificate_returns_404_for_missing_certificate(client):
    response = client.get("/api/certificates/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate not found"
