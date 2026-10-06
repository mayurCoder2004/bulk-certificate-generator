from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.job import GenerationJobCreate
from app.schemas.recipient import RecipientCreate


def test_valid_recipient():
    recipient = RecipientCreate(
        name="Mayur Pawar",
        email="mayur@example.com",
    )

    assert recipient.name == "Mayur Pawar"
    assert str(recipient.email) == "mayur@example.com"


def test_invalid_email():
    with pytest.raises(ValidationError):
        RecipientCreate(
            name="Mayur Pawar",
            email="invalid-email",
        )


def test_empty_recipient_list():
    with pytest.raises(ValidationError):
        GenerationJobCreate(
            event_name="Python Workshop",
            certificate_title="Certificate of Completion",
            organization="Aereo Learning",
            event_date=date(2026, 10, 6),
            recipients=[],
        )


def test_missing_required_field():
    with pytest.raises(ValidationError):
        GenerationJobCreate(
            certificate_title="Certificate of Completion",
            organization="Aereo Learning",
            event_date=date(2026, 10, 6),
            recipients=[
                {
                    "name": "Mayur Pawar",
                    "email": "mayur@example.com",
                }
            ],
        )


def test_recipient_limit():
    recipients = [
        {
            "name": f"User {i}",
            "email": f"user{i}@example.com",
        }
        for i in range(5001)
    ]

    with pytest.raises(ValidationError):
        GenerationJobCreate(
            event_name="Python Workshop",
            certificate_title="Certificate of Completion",
            organization="Aereo Learning",
            event_date=date(2026, 10, 6),
            recipients=recipients,
        )
