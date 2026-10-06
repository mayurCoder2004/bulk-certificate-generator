import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import jobs
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
def client(db, monkeypatch):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    monkeypatch.setattr(
        jobs,
        "run_certificate_job",
        lambda job_id: None,
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_job(client):
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Python Workshop",
            "certificate_title": "Certificate of Completion",
            "organization": "Aereo Learning",
            "event_date": "2026-10-06",
            "recipients": [
                {
                    "name": "Mayur Pawar",
                    "email": "mayur@example.com",
                },
                {
                    "name": "Rahul Sharma",
                    "email": "rahul@example.com",
                },
            ],
        },
    )

    assert response.status_code == 202

    data = response.json()

    assert isinstance(data["job_id"], int)
    assert data["job_id"] > 0
    assert data["status"] == "QUEUED"
    assert data["total_recipients"] == 2


def test_job_and_recipients_are_persisted(client, db):
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Python Workshop",
            "certificate_title": "Certificate of Completion",
            "organization": "Aereo Learning",
            "event_date": "2026-10-06",
            "recipients": [
                {
                    "name": "Mayur Pawar",
                    "email": "mayur@example.com",
                },
                {
                    "name": "Rahul Sharma",
                    "email": "rahul@example.com",
                },
            ],
        },
    )

    assert response.status_code == 202

    job_id = response.json()["job_id"]

    job = (
        db.query(GenerationJob)
        .filter_by(id=job_id)
        .first()
    )

    assert job is not None
    assert job.event_name == "Python Workshop"
    assert job.certificate_title == "Certificate of Completion"
    assert job.organization == "Aereo Learning"
    assert job.total_recipients == 2
    assert job.status == "QUEUED"

    recipients = (
        db.query(Recipient)
        .filter_by(job_id=job_id)
        .order_by(Recipient.id)
        .all()
    )

    assert len(recipients) == 2

    assert recipients[0].name == "Mayur Pawar"
    assert recipients[0].email == "mayur@example.com"
    assert recipients[0].status == "QUEUED"

    assert recipients[1].name == "Rahul Sharma"
    assert recipients[1].email == "rahul@example.com"
    assert recipients[1].status == "QUEUED"
