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


Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_job():
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

    assert data["job_id"] == 1
    assert data["status"] == "QUEUED"
    assert data["total_recipients"] == 2


def test_job_and_recipients_are_persisted():
    db = TestingSessionLocal()

    try:
        job = db.query(GenerationJob).filter_by(id=1).first()

        assert job is not None
        assert job.event_name == "Python Workshop"
        assert job.total_recipients == 2

        recipients = (
            db.query(Recipient)
            .filter_by(job_id=job.id)
            .order_by(Recipient.id)
            .all()
        )

        assert len(recipients) == 2
        assert recipients[0].name == "Mayur Pawar"
        assert recipients[1].name == "Rahul Sharma"
        assert all(
            recipient.status == "QUEUED"
            for recipient in recipients
        )

    finally:
        db.close()