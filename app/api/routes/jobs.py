from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import GenerationJob, Recipient
from app.schemas.job import GenerationJobCreate, GenerationJobCreateResponse
from app.schemas.job_status import (
    GenerationJobStatusResponse,
    RecipientStatusResponse,
)
from app.workers.certificate_worker import run_certificate_job


router = APIRouter(
    prefix="/api/jobs",
    tags=["Jobs"],
)


@router.post(
    "",
    response_model=GenerationJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_job(
    request: GenerationJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = GenerationJob(
        event_name=request.event_name,
        certificate_title=request.certificate_title,
        organization=request.organization,
        event_date=request.event_date,
        status="QUEUED",
        total_recipients=len(request.recipients),
        completed_count=0,
        failed_count=0,
    )

    db.add(job)
    db.flush()

    for recipient_data in request.recipients:
        recipient = Recipient(
            job_id=job.id,
            name=recipient_data.name,
            email=str(recipient_data.email),
            status="QUEUED",
        )

        db.add(recipient)

    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_certificate_job,
        job.id,
    )

    return GenerationJobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_recipients,
    )


@router.get(
    "/{job_id}",
    response_model=GenerationJobStatusResponse,
)
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = (
        db.query(GenerationJob)
        .filter_by(id=job_id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.total_recipients == 0:
        progress = 0.0
    else:
        processed_count = (
            job.completed_count + job.failed_count
        )

        progress = (
            processed_count / job.total_recipients
        ) * 100

    recipients = (
        db.query(Recipient)
        .filter_by(job_id=job_id)
        .order_by(Recipient.id)
        .all()
    )

    recipient_statuses = [
        RecipientStatusResponse(
            recipient_id=recipient.id,
            name=recipient.name,
            email=recipient.email,
            status=recipient.status,
            error_message=recipient.error_message,
        )
        for recipient in recipients
    ]

    return GenerationJobStatusResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_recipients,
        completed_count=job.completed_count,
        failed_count=job.failed_count,
        progress=round(progress, 2),
        recipients=recipient_statuses,
    )
