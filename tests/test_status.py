from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import GenerationJob, Recipient
from app.main import app


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
def db():
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


def test_get_job_status(client, db):
    job = GenerationJob(
        event_name="Python Workshop",
        certificate_title="Certificate of Completion",
        organization="Aereo Learning",
        event_date=date(2026, 10, 6),
        status="COMPLETED_WITH_ERRORS",
        total_recipients=4,
        completed_count=3,
        failed_count=1,
    )

    db.add(job)
    db.flush()

    recipients = [
        Recipient(
            job_id=job.id,
            name="Mayur Pawar",
            email="mayur@example.com",
            status="COMPLETED",
            certificate_path="generated/1/1.pdf",
        ),
        Recipient(
            job_id=job.id,
            name="Rahul Sharma",
            email="rahul@example.com",
            status="COMPLETED",
            certificate_path="generated/1/2.pdf",
        ),
        Recipient(
            job_id=job.id,
            name="Priya Singh",
            email="priya@example.com",
            status="FAILED",
            error_message="Certificate generation failed",
        ),
        Recipient(
            job_id=job.id,
            name="Amit Kumar",
            email="amit@example.com",
            status="COMPLETED",
            certificate_path="generated/1/4.pdf",
        ),
    ]

    db.add_all(recipients)
    db.commit()

    response = client.get(f"/api/jobs/{job.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == job.id
    assert data["status"] == "COMPLETED_WITH_ERRORS"
    assert data["total_recipients"] == 4
    assert data["completed_count"] == 3
    assert data["failed_count"] == 1
    assert data["progress"] == 100.0

    assert len(data["recipients"]) == 4

    assert data["recipients"][0]["name"] == "Mayur Pawar"
    assert data["recipients"][0]["status"] == "COMPLETED"

    assert data["recipients"][2]["name"] == "Priya Singh"
    assert data["recipients"][2]["status"] == "FAILED"
    assert (
        data["recipients"][2]["error_message"]
        == "Certificate generation failed"
    )


def test_get_job_status_returns_404_for_missing_job(client):
    response = client.get("/api/jobs/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
