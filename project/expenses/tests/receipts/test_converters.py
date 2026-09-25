import pytest

from ...receipts.converters import (
    amount,
    cell,
    is_deposit,
    is_money,
    lines,
    money,
)
from ...receipts.errors import UnreadableReceiptTextError
from ...receipts.layout import DEFAULT_UNIT_WORDS


def test_cell_none_becomes_empty_string():
    assert cell(None) == ""


def test_cell_collapses_line_breaks_and_whitespace():
    assert cell("Suma su\nnuolaida") == "Suma su nuolaida"
    assert cell("… BIONATURAL, 250\nml") == "… BIONATURAL, 250 ml"


def test_cell_strips_surrounding_whitespace():
    assert cell("  Prekė  ") == "Prekė"


def test_cell_collapses_runs_of_whitespace():
    assert cell("A    B") == "A B"


def test_lines_none_becomes_no_lines():
    assert lines(None) == ()


def test_lines_keeps_line_breaks_and_cleans_each_line():
    assert lines(" Milk   3,95 A\n2,49 X 0,224 kg ") == (
        "Milk 3,95 A",
        "2,49 X 0,224 kg",
    )


@pytest.mark.parametrize(
    "text,expected",
    [
        ("€2,80", 280),
        ("€71,35", 7135),
        ("€0,40", 40),
        ("€5,99", 599),
    ],
)
def test_money_reads_euro_text_as_cents(text, expected):
    assert money(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "€", "€2,8x"])
def test_money_raises_on_unreadable_text(text):
    with pytest.raises(UnreadableReceiptTextError):
        money(text)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("3,95", 395),
        ("-0,16", -16),
        ("-1,06", -106),
    ],
)
def test_money_reads_maxima_text_as_cents(text, expected):
    assert money(text) == expected


@pytest.mark.parametrize("text", ["3.95", "3,9", "abc", "", "-€0,16", "€-0,16"])
def test_money_raises_on_unreadable_maxima_text(text):
    with pytest.raises(UnreadableReceiptTextError):
        money(text)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("6 vnt.", 6),
        ("1 vnt.", 1),
        ("2 vnt.", 2),
        ("0,404 kg", 1),
        ("1,892 kg", 1),
        ("0,26 kg", 1),
    ],
)
def test_amount_reads_pieces_and_weight(text, expected):
    assert amount(text, DEFAULT_UNIT_WORDS) == expected


@pytest.mark.parametrize("text", ["1,5 vnt.", "3 pcs", "", "abc"])
def test_amount_raises_on_unreadable_text(text):
    with pytest.raises(UnreadableReceiptTextError):
        amount(text, DEFAULT_UNIT_WORDS)


def test_is_deposit_true_for_can():
    title = "Skardinė (depozitinė) 0,10 EUR, 1 vnt. (UŽSTATAS)"

    assert is_deposit(title, ("UŽSTATAS",)) is True


def test_is_deposit_true_for_pet():
    title = "PET (depozitinis) 0,10 EUR, 1 vnt. (UŽSTATAS)"

    assert is_deposit(title, ("UŽSTATAS",)) is True


def test_is_deposit_false_for_ordinary_line():
    title = "Bananai, nuo 20 cm, 1 kg"

    assert is_deposit(title, ("UŽSTATAS",)) is False


@pytest.mark.parametrize("text", ["2,49", "€2,49", "-0,16"])
def test_is_money_true_for_money_text(text):
    assert is_money(text)


@pytest.mark.parametrize("text", ["Pack 3", "3", ""])
def test_is_money_false_for_other_text(text):
    assert not is_money(text)
