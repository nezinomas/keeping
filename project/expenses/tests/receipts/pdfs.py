from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FIXTURES = Path(__file__).parent.parent / "fixtures" / "receipts"


def table_pdf(
    path: Path, *, text_above: str, header: tuple[str, ...], rows, more_tables=()
) -> Path:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    story = [Paragraph(text_above, styles["Normal"])]
    for table_rows in ([header, *rows], *more_tables):
        table = Table([list(row) for row in table_rows])
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
        story += [table, Spacer(1, 12)]

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
