from pydantic import BaseModel


class RecipientStatusResponse(BaseModel):
    recipient_id: int
    name: str
    email: str
    status: str
    error_message: str | None = None


class GenerationJobStatusResponse(BaseModel):
    job_id: int
    status: str
    total_recipients: int
    completed_count: int
    failed_count: int
    progress: float
    recipients: list[RecipientStatusResponse]
