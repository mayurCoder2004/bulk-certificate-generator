from datetime import date

from pydantic import BaseModel, Field

from app.schemas.recipient import RecipientCreate


class GenerationJobCreate(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=255)
    certificate_title: str = Field(..., min_length=1, max_length=255)
    organization: str = Field(..., min_length=1, max_length=255)
    event_date: date
    recipients: list[RecipientCreate] = Field(..., min_length=1, max_length=5000)


class GenerationJobCreateResponse(BaseModel):
    job_id: int
    status: str
    total_recipients: int
