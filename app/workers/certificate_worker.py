from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import GenerationJob, Recipient
from app.services.certificate_service import generate_certificate


def process_certificate_job(
    db: Session,
    job_id: int,
) -> None:
    job = db.query(GenerationJob).filter_by(id=job_id).first()

    if job is None:
        return

    job.status = "PROCESSING"
    db.commit()

    recipients = (
        db.query(Recipient)
        .filter_by(job_id=job_id, status="QUEUED")
        .order_by(Recipient.id)
        .all()
    )

    for recipient in recipients:
        recipient.status = "PROCESSING"
        db.commit()

        try:
            certificate_path = generate_certificate(
                job=job,
                recipient=recipient,
            )

            recipient.certificate_path = certificate_path
            recipient.status = "COMPLETED"
            recipient.error_message = None

            job.completed_count += 1

        except Exception as exc:
            recipient.status = "FAILED"
            recipient.error_message = str(exc)

            job.failed_count += 1

        db.commit()

    if job.failed_count == 0:
        job.status = "COMPLETED"
    elif job.completed_count == 0:
        job.status = "FAILED"
    else:
        job.status = "COMPLETED_WITH_ERRORS"

    db.commit()


def run_certificate_job(job_id: int) -> None:
    db = SessionLocal()

    try:
        process_certificate_job(
            db=db,
            job_id=job_id,
        )
    finally:
        db.close()
