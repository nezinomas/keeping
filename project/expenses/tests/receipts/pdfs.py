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

from ...receipts.layout import TextLayout

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


EMPTY_TEXT_LAYOUT = TextLayout(
    marker="CORNER SHOP LTD",
    lines_start="Items:",
    lines_end="-----",
    vat_classes=("A",),
    amount_separator=" x ",
    item_discount_prefixes=("Deal on:",),
    shop_money_label="Paid with points",
    total_label="Total due",
)


def empty_text_receipt_pdf(path: Path) -> Path:
    """A receipt of EMPTY_TEXT_LAYOUT with Shop money but no lines."""
    return text_pdf(
        path,
        [
            "CORNER SHOP LTD",
            "Items:",
            "-----",
            "Paid with points -0,30 A",
            "Total due 0,00",
        ],
    )
