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


@pytest.mark.parametrize(
    ("read", "expected"),
    [
        pytest.param(
            lambda receipt: [line.title for line in receipt.lines],
            ["Bread", "Farmhouse cheese wedge", "Butter"],
            id="titles_in_order_with_a_split_title_joined",
        ),
        pytest.param(
            lambda receipt: receipt.lines[1].price,
            200,
            id="deal_discount_folded_into_the_split_title_line",
        ),
        pytest.param(
            lambda receipt: receipt.lines[0].amount,
            3,
            id="amount_line_read_for_the_line_above",
        ),
        pytest.param(
            lambda receipt: receipt.lines[2].amount,
            1,
            id="amount_defaults_to_one_piece",
        ),
        pytest.param(lambda receipt: receipt.total, 540, id="total"),
        pytest.param(lambda receipt: receipt.shop_money, 30, id="shop_money"),
    ],
)
def test_text_receipt_parser_reads_the_base_receipt(tmp_path, read, expected):
    receipt = _receipt(tmp_path, BASE_LINES)

    assert read(receipt) == expected


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


@pytest.mark.parametrize(
    ("lines", "names"),
    [
        pytest.param(
            ["CORNER SHOP LTD", "Bread 1,20 A", "-----", "Total due 1,20"],
            "Items:",
            id="no_lines_start_marker",
        ),
        pytest.param(
            ["CORNER SHOP LTD", "Items:", "Bread 1,20 A", "Total due 1,20"],
            "-----",
            id="no_lines_end_marker",
        ),
        pytest.param(
            ["CORNER SHOP LTD", "Items:", "Bread 1,20 A", "-----"],
            "Total due",
            id="no_total_line",
        ),
        pytest.param(
            [
                "CORNER SHOP LTD",
                "Items:",
                "Deal on: something -0,50 A",
                "-----",
                "Total due 1,00",
            ],
            "Deal on: something -0,50 A",
            id="deal_prefix_discount_with_no_line_above",
        ),
        pytest.param(
            [
                "CORNER SHOP LTD",
                "Items:",
                "Markdown -0,20 A",
                "-----",
                "Total due 1,00",
            ],
            "Markdown -0,20 A",
            id="markdown_prefix_discount_with_no_line_above",
        ),
        pytest.param(
            [
                "CORNER SHOP LTD",
                "Items:",
                "Bread 1,20 A",
                "-----",
                "Total due soon",
            ],
            "Total due soon",
            id="total_without_money",
        ),
        pytest.param(
            ["CORNER SHOP LTD", "Items:", "0,40 x 3 vnt.", "-----", "Total due 1,00"],
            "0,40 x 3 vnt.",
            id="amount_line_with_no_line_above",
        ),
        pytest.param(
            ["CORNER SHOP LTD", "Items:", "Bread", "-----", "Total due 1,00"],
            "Bread",
            id="title_without_a_price",
        ),
        pytest.param(
            ["CORNER SHOP LTD", "Items:", "Milk 1,20 C", "-----", "Total due 1,20"],
            "Milk 1,20 C",
            id="unknown_vat_letter_on_a_line",
        ),
        pytest.param(
            [
                "CORNER SHOP LTD",
                "Items:",
                "Bread 1,20 A",
                "Deal on: bread",
                "-----",
                "Total due 1,20",
            ],
            "Deal on: bread",
            id="discount_without_a_price",
        ),
        pytest.param(
            [
                "CORNER SHOP LTD",
                "Items:",
                "Bread",
                "0,40 x 3 vnt.",
                "-----",
                "Total due 1,00",
            ],
            "0,40 x 3 vnt.",
            id="title_then_an_amount_line",
        ),
        pytest.param(
            [
                "CORNER SHOP LTD",
                "Items:",
                "Bread",
                "Deal on: Bread -0,10 A",
                "-----",
                "Total due 1,00",
            ],
            "Deal on: Bread -0,10 A",
            id="title_then_a_discount_line",
        ),
        pytest.param(
            [
                "CORNER SHOP LTD",
                "Items:",
                "Bread 1,20 A",
                "Deal on: Bread -0,10 C",
                "-----",
                "Total due 1,10",
            ],
            "Deal on: Bread -0,10 C",
            id="unknown_vat_letter_in_a_discount",
        ),
    ],
)
def test_text_receipt_parser_raises_on_a_receipt_it_cannot_read(tmp_path, lines, names):
    with pytest.raises(UnreadableReceiptTextError) as error:
        _receipt(tmp_path, lines)

    assert str(error.value) == names


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


class _TextPage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class _TextDocument:
    def __init__(self, *texts):
        self.pages = [_TextPage(text) for text in texts]


def test_text_receipt_parser_skips_blank_lines_between_items():
    document = _TextDocument(
        "CORNER SHOP LTD\nItems:\nBread 1,20 A\n\nButter 2,00 A\n-----\nTotal due 3,20"
    )

    receipt = TextReceiptParser(LAYOUT).parse(document)

    assert [line.title for line in receipt.lines] == ["Bread", "Butter"]


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

    with (
        pdfplumber.open(path) as document,
        pytest.raises(UnreadableReceiptTextError) as error,
    ):
        TextReceiptParser(LAYOUT).parse(document)

    assert str(error.value) == "-----"


def test_text_receipt_parser_reads_a_total_on_a_later_page(tmp_path):
    path = text_pdf(
        tmp_path / "receipt.pdf",
        ["CORNER SHOP LTD", "Items:", "Bread 1,20 A", "-----"],
        more_pages=(["Total due 1,20"],),
    )

    with pdfplumber.open(path) as document:
        receipt = TextReceiptParser(LAYOUT).parse(document)

    assert receipt.total == 120
