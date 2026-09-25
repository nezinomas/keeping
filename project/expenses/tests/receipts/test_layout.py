import pytest

from ...receipts.layout import (
    DEFAULT_DEPOSIT_WORDS,
    DEFAULT_UNIT_WORDS,
    Columns,
    TableLayout,
    TextLayout,
    Unit,
)


def test_unit_values():
    assert Unit.PIECES == "pieces"
    assert Unit.WEIGHT == "weight"


def test_default_unit_words():
    assert DEFAULT_UNIT_WORDS["vnt"] == Unit.PIECES
    assert DEFAULT_UNIT_WORDS["kg"] == Unit.WEIGHT


def test_default_unit_words_is_read_only():
    with pytest.raises(TypeError):
        DEFAULT_UNIT_WORDS["new"] = Unit.PIECES


def test_default_deposit_words():
    assert DEFAULT_DEPOSIT_WORDS == ("UŽSTATAS",)


def test_columns_holds_header_text():
    columns = Columns(title="Prekė", amount="Kiekis", price="Kaina")

    assert columns.title == "Prekė"
    assert columns.amount == "Kiekis"
    assert columns.price == "Kaina"


def test_table_layout_defaults_to_shared_words():
    layout = TableLayout(
        marker="Shop",
        columns=Columns(title="Prekė", amount="Kiekis", price="Kaina"),
        total_label="Suma",
    )

    assert layout.unit_words == DEFAULT_UNIT_WORDS
    assert layout.deposit_words == DEFAULT_DEPOSIT_WORDS


def test_layout_adding_a_word_keeps_the_defaults():
    layout = TableLayout(
        marker="Shop",
        columns=Columns(title="Prekė", amount="Kiekis", price="Kaina"),
        total_label="Suma",
        unit_words=DEFAULT_UNIT_WORDS | {"g": Unit.WEIGHT},
        deposit_words=DEFAULT_DEPOSIT_WORDS + ("DEPOSIT",),
    )

    assert layout.unit_words["vnt"] == Unit.PIECES
    assert layout.unit_words["kg"] == Unit.WEIGHT
    assert layout.unit_words["g"] == Unit.WEIGHT
    assert "UŽSTATAS" in layout.deposit_words
    assert "DEPOSIT" in layout.deposit_words


def test_text_layout_holds_its_fields():
    layout = TextLayout(
        marker="Shop",
        lines_start="Items:",
        lines_end="-----",
        vat_classes=("A", "B"),
        amount_separator=" x ",
        item_discount_prefixes=("Deal:",),
        shop_money_label="Paid",
        total_label="Total",
    )

    assert layout.marker == "Shop"
    assert layout.lines_start == "Items:"
    assert layout.lines_end == "-----"
    assert layout.vat_classes == ("A", "B")
    assert layout.amount_separator == " x "
    assert layout.item_discount_prefixes == ("Deal:",)
    assert layout.shop_money_label == "Paid"
    assert layout.total_label == "Total"


def test_text_layout_item_discount_prefixes_is_a_tuple():
    layout = TextLayout(
        marker="Shop",
        lines_start="Items:",
        lines_end="-----",
        vat_classes=("A",),
        amount_separator=" x ",
        item_discount_prefixes=("Deal:", "Markdown"),
        shop_money_label="Paid",
        total_label="Total",
    )

    assert layout.item_discount_prefixes == ("Deal:", "Markdown")


def test_text_layout_defaults_to_shared_words():
    layout = TextLayout(
        marker="Shop",
        lines_start="Items:",
        lines_end="-----",
        vat_classes=("A",),
        amount_separator=" x ",
        item_discount_prefixes=("Deal:",),
        shop_money_label="Paid",
        total_label="Total",
    )

    assert layout.unit_words == DEFAULT_UNIT_WORDS
    assert layout.deposit_words == DEFAULT_DEPOSIT_WORDS


def test_text_layout_adding_a_word_keeps_the_defaults():
    layout = TextLayout(
        marker="Shop",
        lines_start="Items:",
        lines_end="-----",
        vat_classes=("A",),
        amount_separator=" x ",
        item_discount_prefixes=("Deal:",),
        shop_money_label="Paid",
        total_label="Total",
        unit_words=DEFAULT_UNIT_WORDS | {"g": Unit.WEIGHT},
        deposit_words=DEFAULT_DEPOSIT_WORDS + ("DEPOSIT",),
    )

    assert layout.unit_words["g"] == Unit.WEIGHT
    assert "UŽSTATAS" in layout.deposit_words
    assert "DEPOSIT" in layout.deposit_words
