import pdfplumber
import pytest

from ...receipts.errors import UnreadableReceiptTextError
from ...receipts.layout import TextLayout
from ...receipts.shop_parser import ShopParser
from ...receipts.text_parser import TextReceiptParser
from .pdfs import text_pdf

LAYOUT = TextLayout(
    marker="CORNER SHOP LTD",
    lines_start="Items:",
    lines_end="-----",
    vat_classes=("A", "B"),
    amount_separator=" x ",
    item_discount_prefixes=("Deal on:", "Markdown"),
    shop_money_label="Paid with points",
    total_label="Total due",
)

BASE_LINES = [
    "CORNER SHOP LTD",
    "Some header line",
    "Items:",
    "Bread 1,20 A",
    "0,40 x 3 vnt.",
    "Farmhouse cheese",
    "wedge 2,50 B",
    "Deal on: wedge cheese -0,50 B",
    "Butter 2,00 A",
    "-----",
    "Some footer line",
    "Paid with points -0,30 A",
    "Total due 5,40",
]


def _receipt(tmp_path, lines):
    path = text_pdf(tmp_path / "receipt.pdf", lines)
    with pdfplumber.open(path) as document:
        return TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_satisfies_shop_parser_protocol():
    parser: ShopParser = TextReceiptParser(LAYOUT)

    assert parser.recognises("Welcome to CORNER SHOP LTD")
    assert not parser.recognises("OTHER SHOP")


def test_text_receipt_parser_reads_lines_in_order(tmp_path):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert [line.title for line in receipt.lines] == [
        "Bread",
        "Farmhouse cheese wedge",
        "Butter",
    ]


def test_text_receipt_parser_joins_a_title_split_across_two_lines(tmp_path):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert receipt.lines[1].title == "Farmhouse cheese wedge"
    assert receipt.lines[1].price == 200


def test_text_receipt_parser_reads_an_amount_line_for_the_line_above(tmp_path):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert receipt.lines[0].amount == 3


def test_text_receipt_parser_folds_an_item_discount_into_the_line_above(tmp_path):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert receipt.lines[1].price == 200


def test_text_receipt_parser_folds_a_second_discount_prefix_into_the_line_above(
    tmp_path,
):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Bread 1,20 A",
        "Markdown -0,20 A",
        "-----",
        "Total due 1,00",
    ]

    receipt = _receipt(tmp_path, lines)

    assert receipt.lines[0].price == 100


def test_text_receipt_parser_raises_on_second_prefix_discount_with_no_line_above(
    tmp_path,
):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Markdown -0,20 A",
        "-----",
        "Total due 1,00",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_defaults_amount_to_one_piece(tmp_path):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert receipt.lines[2].title == "Butter"
    assert receipt.lines[2].amount == 1


def test_text_receipt_parser_ignores_lines_outside_the_region(tmp_path):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert len(receipt.lines) == 3


def test_text_receipt_parser_reads_the_total(tmp_path):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert receipt.total == 540


def test_text_receipt_parser_reads_shop_money(tmp_path):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert receipt.shop_money == 30


def test_text_receipt_parser_defaults_shop_money_to_zero_when_absent(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Bread 1,20 A",
        "-----",
        "Total due 1,20",
    ]

    receipt = _receipt(tmp_path, lines)

    assert receipt.shop_money == 0
    assert receipt.agrees


def test_text_receipt_parser_raises_on_discount_with_no_line_above(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Deal on: something -0,50 A",
        "-----",
        "Total due 1,00",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_on_amount_line_with_no_line_above(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "0,40 x 3 vnt.",
        "-----",
        "Total due 1,00",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_on_a_title_left_without_a_price(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Bread",
        "-----",
        "Total due 1,00",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_on_a_title_followed_by_an_amount_line(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Bread",
        "0,40 x 3 vnt.",
        "-----",
        "Total due 1,00",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_on_a_title_followed_by_a_discount_line(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Bread",
        "Deal on: Bread -0,10 A",
        "-----",
        "Total due 1,00",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_on_unknown_vat_letter(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Milk 1,20 C",
        "-----",
        "Total due 1,20",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_on_unknown_vat_letter_in_a_discount(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Bread 1,20 A",
        "Deal on: Bread -0,10 C",
        "-----",
        "Total due 1,10",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_when_no_lines_start(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Bread 1,20 A",
        "-----",
        "Total due 1,20",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_when_no_lines_end(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Bread 1,20 A",
        "Total due 1,20",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_raises_when_no_total_line(tmp_path):
    lines = [
        "CORNER SHOP LTD",
        "Items:",
        "Bread 1,20 A",
        "-----",
    ]

    with (
        pdfplumber.open(text_pdf(tmp_path / "r.pdf", lines)) as document,
        pytest.raises(UnreadableReceiptTextError),
    ):
        TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_reads_a_title_holding_the_separator(tmp_path):
    lines = BASE_LINES.copy()
    lines[lines.index("Butter 2,00 A")] = "Pack 3 x 2 bags 4,99 A"

    receipt = _receipt(tmp_path, lines)

    assert receipt.lines[2].title == "Pack 3 x 2 bags"
    assert receipt.lines[2].price == 499


def test_text_receipt_parser_raises_when_the_lines_cross_a_page(tmp_path):
    path = text_pdf(
        tmp_path / "receipt.pdf",
        ["CORNER SHOP LTD", "Items:", "Bread 1,20 A", "1 of 2"],
        more_pages=(["Butter 2,00 A", "-----", "Total due 3,20"],),
    )

    with pdfplumber.open(path) as document:
        with pytest.raises(UnreadableReceiptTextError):
            TextReceiptParser(LAYOUT).parse(document)


def test_text_receipt_parser_reads_a_total_on_a_later_page(tmp_path):
    path = text_pdf(
        tmp_path / "receipt.pdf",
        ["CORNER SHOP LTD", "Items:", "Bread 1,20 A", "-----"],
        more_pages=(["Total due 1,20"],),
    )

    with pdfplumber.open(path) as document:
        receipt = TextReceiptParser(LAYOUT).parse(document)

    assert receipt.total == 120
