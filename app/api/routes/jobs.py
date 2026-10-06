from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import GenerationJob, Recipient
from app.schemas.job import GenerationJobCreate, GenerationJobCreateResponse


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

    return GenerationJobCreateResponse(
        job_id=job.id,
        status=job.status,
        total_recipients=job.total_recipients,
    )
