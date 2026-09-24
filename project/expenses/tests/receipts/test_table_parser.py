import pdfplumber
import pytest

from ...receipts.errors import UnreadableReceiptTextError
from ...receipts.layout import (
    DEFAULT_DEPOSIT_WORDS,
    Columns,
    TableLayout,
)
from ...receipts.shop_parser import ShopParser
from ...receipts.table_parser import TableReceiptParser
from .pdfs import table_pdf

LAYOUT = TableLayout(
    marker="ACME SHOP",
    columns=Columns(title="Item", amount="Qty", price="Sum paid"),
    total_label="Grand total",
    deposit_words=DEFAULT_DEPOSIT_WORDS + ("DEPOSIT",),
)


def _acme_pdf(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [
        ("1", "Apple", "2 vnt.", "€1,20"),
        ("2", "Bottle (DEPOSIT)", "1 vnt.", "€0,10"),
        ("3", "Pear", "0,5 kg", "€0,80"),
        ("", "Discount 10%", "", "€0,20"),
        ("", "Grand total", "", "€2,30"),
    ]
    return table_pdf(
        tmp_path / "acme.pdf", text_above="ACME SHOP", header=header, rows=rows
    )


def test_table_receipt_parser_reads_lines_in_order(tmp_path):
    path = _acme_pdf(tmp_path)
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert [line.title for line in receipt.lines] == [
        "Apple",
        "Bottle (DEPOSIT)",
        "Pear",
    ]


def test_table_receipt_parser_reads_amounts_and_prices(tmp_path):
    path = _acme_pdf(tmp_path)
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert receipt.lines[0].amount == 2
    assert receipt.lines[0].price == 120
    assert receipt.lines[2].amount == 1
    assert receipt.lines[2].price == 80


def test_table_receipt_parser_flags_deposit_line(tmp_path):
    path = _acme_pdf(tmp_path)
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert receipt.lines[1].is_deposit is True
    assert receipt.lines[0].is_deposit is False


def test_table_receipt_parser_reads_total(tmp_path):
    path = _acme_pdf(tmp_path)
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert receipt.total == 230


def test_table_receipt_parser_stops_at_first_empty_amount_cell(tmp_path):
    path = _acme_pdf(tmp_path)
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert len(receipt.lines) == 3


def test_table_receipt_parser_raises_when_no_table_carries_the_headers(tmp_path):
    path = table_pdf(
        tmp_path / "no_match.pdf",
        text_above="ACME SHOP",
        header=("A", "B", "C"),
        rows=[("1", "2", "3")],
    )
    with pdfplumber.open(path) as document:
        with pytest.raises(UnreadableReceiptTextError):
            TableReceiptParser(LAYOUT).parse(document)


def test_table_receipt_parser_raises_when_no_total_row(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [("1", "Apple", "2 vnt.", "€1,20")]
    path = table_pdf(
        tmp_path / "no_total.pdf", text_above="ACME SHOP", header=header, rows=rows
    )
    with pdfplumber.open(path) as document:
        with pytest.raises(UnreadableReceiptTextError):
            TableReceiptParser(LAYOUT).parse(document)


def test_table_receipt_parser_satisfies_shop_parser_protocol():
    parser: ShopParser = TableReceiptParser(LAYOUT)

    assert parser.recognises("Receipt from ACME SHOP")
    assert not parser.recognises("Receipt from OTHER SHOP")


def test_table_receipt_parser_raises_on_a_product_row_after_a_blank_amount(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [
        ("1", "Apple", "2 vnt.", "€1,20"),
        ("2", "Plum", "", "€0,50"),
        ("3", "Pear", "1 vnt.", "€0,80"),
        ("", "Grand total", "", "€2,50"),
    ]
    path = table_pdf(
        tmp_path / "gap.pdf", text_above="ACME SHOP", header=header, rows=rows
    )
    with pdfplumber.open(path) as document, pytest.raises(UnreadableReceiptTextError):
        TableReceiptParser(LAYOUT).parse(document)
