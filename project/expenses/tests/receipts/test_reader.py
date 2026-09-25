from io import BytesIO

import pdfplumber
import pytest

from ...receipts import converters
from ...receipts.errors import UnreadableReceiptTextError, UnrecognisedReceiptError
from ...receipts.reader import PARSERS, ReceiptReader
from .pdfs import FIXTURES, table_pdf

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


@pytest.mark.parametrize("fixture", [FIXTURES / "barbora.pdf", FIXTURES / "maxima.pdf"])
def test_each_fixture_is_recognised_by_exactly_one_parser(fixture):
    text = _text(fixture)

    matches = [parser for parser in PARSERS if parser.recognises(text)]

    assert len(matches) == 1
