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
    promotion_label="Promo applied",
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
    with (
        pdfplumber.open(path) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TableReceiptParser(LAYOUT).parse(document)


def test_table_receipt_parser_raises_when_no_total_row(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [("1", "Apple", "2 vnt.", "€1,20")]
    path = table_pdf(
        tmp_path / "no_total.pdf", text_above="ACME SHOP", header=header, rows=rows
    )
    with (
        pdfplumber.open(path) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
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


def test_table_receipt_parser_reads_a_continuation_table(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    first_table = [header, ("1", "Apple", "2 vnt.", "€1,20")]
    second_table = [
        ("2", "Pear", "1 vnt.", "€0,80"),
        ("", "Grand total", "", "€2,00"),
    ]
    path = table_pdf(
        tmp_path / "continuation.pdf",
        text_above="ACME SHOP",
        header=first_table[0],
        rows=first_table[1:],
        more_tables=(second_table,),
    )
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert [line.title for line in receipt.lines] == ["Apple", "Pear"]
    assert receipt.total == 200


def test_table_receipt_parser_ignores_a_narrower_table(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    first_table = [
        header,
        ("1", "Apple", "2 vnt.", "€1,20"),
        ("", "Grand total", "", "€1,20"),
    ]
    narrower_table = [("Deposit", "€0,10")]
    path = table_pdf(
        tmp_path / "narrower.pdf",
        text_above="ACME SHOP",
        header=first_table[0],
        rows=first_table[1:],
        more_tables=(narrower_table,),
    )
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert [line.title for line in receipt.lines] == ["Apple"]


def test_table_receipt_parser_reads_the_total_from_a_separate_table(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    first_table = [header, ("1", "Apple", "2 vnt.", "€1,20")]
    total_table = [("Grand total", "€1,20")]
    path = table_pdf(
        tmp_path / "separate_total.pdf",
        text_above="ACME SHOP",
        header=first_table[0],
        rows=first_table[1:],
        more_tables=(total_table,),
    )
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert receipt.total == 120
    assert [line.title for line in receipt.lines] == ["Apple"]


def test_table_receipt_parser_gives_the_promotion_price_to_the_row_below(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [
        ("1", "Promo applied", "", "€3,49"),
        ("2", "Cucumbers", "2 vnt.", ""),
        ("", "Grand total", "", "€3,49"),
    ]
    path = table_pdf(
        tmp_path / "promo.pdf", text_above="ACME SHOP", header=header, rows=rows
    )
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert len(receipt.lines) == 1
    assert receipt.lines[0].title == "Cucumbers"
    assert receipt.lines[0].amount == 2
    assert receipt.lines[0].price == 349


def test_table_receipt_parser_raises_when_a_promotion_row_is_followed_by_a_priced_row(
    tmp_path,
):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [
        ("1", "Promo applied", "", "€3,49"),
        ("2", "Cucumbers", "2 vnt.", "€1,00"),
        ("", "Grand total", "", "€3,49"),
    ]
    path = table_pdf(
        tmp_path / "promo_priced.pdf", text_above="ACME SHOP", header=header, rows=rows
    )
    with pdfplumber.open(path) as document, pytest.raises(UnreadableReceiptTextError):
        TableReceiptParser(LAYOUT).parse(document)


def test_table_receipt_parser_raises_when_a_promoted_row_was_not_collected(
    tmp_path,
):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [
        ("1", "Promo applied", "", "€3,49"),
        ("", "Cucumbers", "0", ""),
        ("", "Grand total", "", "€3,49"),
    ]
    path = table_pdf(
        tmp_path / "promo_zero.pdf", text_above="ACME SHOP", header=header, rows=rows
    )
    with pdfplumber.open(path) as document, pytest.raises(UnreadableReceiptTextError):
        TableReceiptParser(LAYOUT).parse(document)


def test_table_receipt_parser_raises_when_a_promotion_row_is_last(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [
        ("1", "Apple", "2 vnt.", "€1,20"),
        ("2", "Promo applied", "", "€0,50"),
    ]
    path = table_pdf(
        tmp_path / "promo_last.pdf", text_above="ACME SHOP", header=header, rows=rows
    )
    with pdfplumber.open(path) as document, pytest.raises(UnreadableReceiptTextError):
        TableReceiptParser(LAYOUT).parse(document)


def test_table_receipt_parser_drops_a_not_collected_row(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [
        ("1", "Apple", "2 vnt.", "€1,20"),
        ("2", "Not collected", "0", "€0,00"),
        ("", "Grand total", "", "€1,20"),
    ]
    path = table_pdf(
        tmp_path / "zero_amount.pdf", text_above="ACME SHOP", header=header, rows=rows
    )
    with pdfplumber.open(path) as document:
        receipt = TableReceiptParser(LAYOUT).parse(document)

    assert [line.title for line in receipt.lines] == ["Apple"]


def test_table_receipt_parser_raises_when_a_zero_amount_row_has_a_price(tmp_path):
    header = ("No", "Item", "Qty", "Sum\npaid")
    rows = [
        ("1", "Apple", "2 vnt.", "€1,20"),
        ("2", "Odd row", "0", "€0,50"),
        ("", "Grand total", "", "€1,70"),
    ]
    path = table_pdf(
        tmp_path / "zero_amount_priced.pdf",
        text_above="ACME SHOP",
        header=header,
        rows=rows,
    )
    with pdfplumber.open(path) as document, pytest.raises(UnreadableReceiptTextError):
        TableReceiptParser(LAYOUT).parse(document)
