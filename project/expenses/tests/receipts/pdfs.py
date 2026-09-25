from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

FIXTURES = Path(__file__).parent.parent / "fixtures" / "receipts"


def table_pdf(path: Path, *, text_above: str, header: tuple[str, ...], rows) -> Path:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    story = []

    styles = getSampleStyleSheet()
    story.append(Paragraph(text_above, styles["Normal"]))

    table_data = [list(header)] + [list(row) for row in rows]
    table = Table(table_data)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    story.append(table)

    doc.build(story)
    return path


def text_pdf(path: Path, lines, *, more_pages=()) -> Path:
    pdf = canvas.Canvas(str(path), pagesize=letter)
    for page in (lines, *more_pages):
        y = letter[1] - inch
        for line in page:
            pdf.drawString(0.5 * inch, y, line)
            y -= 14
        pdf.showPage()
    pdf.save()
    return path
