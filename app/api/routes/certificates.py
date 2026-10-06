from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Recipient


router = APIRouter(
    prefix="/api/certificates",
    tags=["Certificates"],
)


@router.get("/{certificate_id}")
def get_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
):
    recipient = (
        db.query(Recipient)
        .filter_by(id=certificate_id)
        .first()
    )

    if recipient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    if recipient.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate is not available",
        )

    if not recipient.certificate_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file not found",
        )

    file_path = Path(recipient.certificate_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file not found",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"certificate_{recipient.id}.pdf",
    )
