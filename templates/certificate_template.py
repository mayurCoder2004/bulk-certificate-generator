from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def draw_certificate(
    pdf: canvas.Canvas,
    recipient_name: str,
    certificate_title: str,
    event_name: str,
    organization: str,
    event_date: str,
) -> None:
    width, height = landscape(A4)

    # Background
    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)

    # Outer border
    pdf.setStrokeColor(colors.HexColor("#1F2937"))
    pdf.setLineWidth(3)
    pdf.rect(25, 25, width - 50, height - 50, fill=0, stroke=1)

    # Inner border
    pdf.setStrokeColor(colors.HexColor("#9CA3AF"))
    pdf.setLineWidth(1)
    pdf.rect(35, 35, width - 70, height - 70, fill=0, stroke=1)

    # Organization
    pdf.setFillColor(colors.HexColor("#374151"))
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, height - 90, organization.upper())

    # Certificate title
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(width / 2, height - 145, certificate_title)

    # Subtitle
    pdf.setFillColor(colors.HexColor("#6B7280"))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(
        width / 2,
        height - 180,
        "This certificate is proudly presented to",
    )

    # Recipient name
    pdf.setFillColor(colors.HexColor("#111827"))
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 230, recipient_name)

    # Name underline
    pdf.setStrokeColor(colors.HexColor("#9CA3AF"))
    pdf.setLineWidth(1)
    pdf.line(
        width / 2 - 150,
        height - 245,
        width / 2 + 150,
        height - 245,
    )

    # Event description
    pdf.setFillColor(colors.HexColor("#374151"))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(
        width / 2,
        height - 285,
        f"for successfully participating in {event_name}",
    )

    # Date
    pdf.setFillColor(colors.HexColor("#6B7280"))
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(
        width / 2,
        95,
        f"Date: {event_date}",
    )

    # Footer
    pdf.setFillColor(colors.HexColor("#374151"))
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(
        width / 2,
        70,
        organization,
    )

    pdf.showPage()
    pdf.save()
