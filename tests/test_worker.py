from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import GenerationJob, Recipient
from app.workers import certificate_worker
from app.workers.certificate_worker import process_certificate_job


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


def test_worker_processes_all_recipients_and_isolates_failure(
    db,
    monkeypatch,
):
    job = GenerationJob(
        event_name="Python Workshop",
        certificate_title="Certificate of Completion",
        organization="Aereo Learning",
        event_date=date(2026, 10, 6),
        status="QUEUED",
        total_recipients=3,
        completed_count=0,
        failed_count=0,
    )

    db.add(job)
    db.flush()

    recipients = [
        Recipient(
            job_id=job.id,
            name="Mayur Pawar",
            email="mayur@example.com",
            status="QUEUED",
        ),
        Recipient(
            job_id=job.id,
            name="Failing User",
            email="failing@example.com",
            status="QUEUED",
        ),
        Recipient(
            job_id=job.id,
            name="Rahul Sharma",
            email="rahul@example.com",
            status="QUEUED",
        ),
    ]

    db.add_all(recipients)
    db.commit()

    def fake_generate_certificate(job, recipient):
        if recipient.name == "Failing User":
            raise RuntimeError(
                "Simulated certificate generation failure"
            )

        return f"generated/{job.id}/{recipient.id}.pdf"

    monkeypatch.setattr(
        certificate_worker,
        "generate_certificate",
        fake_generate_certificate,
    )

    process_certificate_job(
        db=db,
        job_id=job.id,
    )

    db.refresh(job)

    assert job.status == "COMPLETED_WITH_ERRORS"
    assert job.total_recipients == 3
    assert job.completed_count == 2
    assert job.failed_count == 1

    recipients = (
        db.query(Recipient)
        .filter_by(job_id=job.id)
        .order_by(Recipient.id)
        .all()
    )

    assert recipients[0].status == "COMPLETED"
    assert recipients[0].certificate_path is not None

    assert recipients[1].status == "FAILED"
    assert recipients[1].error_message == (
        "Simulated certificate generation failure"
    )

    assert recipients[2].status == "COMPLETED"
    assert recipients[2].certificate_path is not None
