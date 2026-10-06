from datetime import date
from pathlib import Path

from app.db.models import GenerationJob, Recipient
from app.services.certificate_service import generate_certificate


def test_generate_certificate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    job = GenerationJob(
        id=1,
        event_name="Python Workshop",
        certificate_title="Certificate of Completion",
        organization="Aereo Learning",
        event_date=date(2026, 10, 6),
        status="QUEUED",
        total_recipients=1,
        completed_count=0,
        failed_count=0,
    )

    recipient = Recipient(
        id=1,
        job_id=1,
        name="Mayur Pawar",
        email="mayur@example.com",
        status="QUEUED",
    )

    file_path = generate_certificate(job, recipient)

    generated_file = Path(file_path)

    assert generated_file.exists()
    assert generated_file.suffix == ".pdf"
    assert generated_file.stat().st_size > 0
