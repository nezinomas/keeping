from io import BytesIO

import pdfplumber
import pytest

from ...receipts import converters, reader
from ...receipts.errors import UnreadableReceiptTextError, UnrecognisedReceiptError
from ...receipts.layout import Columns, TableLayout
from ...receipts.reader import PARSERS, ReceiptReader
from ...receipts.table_parser import TableReceiptParser
from ...receipts.text_parser import TextReceiptParser
from .pdfs import (
    EMPTY_TEXT_LAYOUT,
    FIXTURES,
    empty_text_receipt_pdf,
    table_pdf,
)

FIXTURE = FIXTURES / "barbora.pdf"


def test_reader_reads_barbora_fixture_into_29_lines():
    receipt = ReceiptReader.read(FIXTURE)

    assert len(receipt.lines) == 29


def test_reader_raises_when_no_parser_recognises_the_pdf(tmp_path):
    path = table_pdf(
        tmp_path / "unknown.pdf",
        text_above="UNKNOWN SHOP",
        header=("Item", "Qty", "Sum"),
        rows=[("Apple", "2 vnt.", "€1,20")],
    )

    with pytest.raises(UnrecognisedReceiptError):
        ReceiptReader.read(path)


def test_reader_raises_unreadable_when_the_file_is_not_a_pdf():
    with pytest.raises(UnreadableReceiptTextError):
        ReceiptReader.read(BytesIO(b"hello, not a pdf"))


def _text(path):
    with pdfplumber.open(path) as document:
        return "\n".join(
            converters.cell(page.extract_text()) for page in document.pages
        )


@pytest.mark.parametrize(
    "fixture",
    [
        FIXTURES / "barbora.pdf",
        FIXTURES / "maxima.pdf",
        FIXTURES / "barbora_promotion.pdf",
        FIXTURES / "barbora_substitute.pdf",
        FIXTURES / "barbora_two_pages.pdf",
        FIXTURES / "maxima_markdown.pdf",
    ],
)
def test_each_fixture_is_recognised_by_exactly_one_parser(fixture):
    text = _text(fixture)

    matches = [parser for parser in PARSERS if parser.recognises(text)]

    assert len(matches) == 1


NO_LINES_TABLE_LAYOUT = TableLayout(
    marker="ACME SHOP",
    columns=Columns(title="Item", amount="Qty", price="Sum"),
    total_label="Grand total",
    promotion_label="Promo applied",
)


def test_reader_raises_unreadable_when_a_text_receipt_has_no_lines(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(reader, "PARSERS", (TextReceiptParser(EMPTY_TEXT_LAYOUT),))
    path = empty_text_receipt_pdf(tmp_path / "empty.pdf")

    with pytest.raises(UnreadableReceiptTextError):
        ReceiptReader.read(path)


def test_reader_raises_unreadable_when_no_table_row_was_collected(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(reader, "PARSERS", (TableReceiptParser(NO_LINES_TABLE_LAYOUT),))
    path = table_pdf(
        tmp_path / "empty.pdf",
        text_above="ACME SHOP",
        header=("Item", "Qty", "Sum"),
        rows=[("Apple", "0", "€0,00"), ("Grand total", "", "€0,00")],
    )

    with pytest.raises(UnreadableReceiptTextError):
        ReceiptReader.read(path)
