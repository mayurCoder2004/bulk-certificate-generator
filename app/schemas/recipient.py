from pydantic import BaseModel, EmailStr, Field


class RecipientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
