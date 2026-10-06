from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from app.db.models import GenerationJob, Recipient
from templates.certificate_template import draw_certificate


GENERATED_DIR = Path("generated")


def generate_certificate(
    job: GenerationJob,
    recipient: Recipient,
) -> str:
    job_directory = GENERATED_DIR / str(job.id)
    job_directory.mkdir(parents=True, exist_ok=True)

    file_path = job_directory / f"{recipient.id}.pdf"

    pdf = canvas.Canvas(
        str(file_path),
        pagesize=landscape(A4),
    )

    draw_certificate(
        pdf=pdf,
        recipient_name=recipient.name,
        certificate_title=job.certificate_title,
        event_name=job.event_name,
        organization=job.organization,
        event_date=job.event_date.strftime("%B %d, %Y"),
    )

    return str(file_path)
