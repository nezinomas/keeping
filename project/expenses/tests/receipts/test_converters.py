import re

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

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


@pytest.mark.parametrize(
    "text,expected",
    [
        pytest.param(None, "", id="none_becomes_empty_string"),
        pytest.param("A    B", "A B", id="collapses_runs_of_whitespace"),
        pytest.param("Suma su\nnuolaida", "Suma su nuolaida", id="line_break_in_text"),
        pytest.param(
            "… BIONATURAL, 250\nml", "… BIONATURAL, 250 ml", id="line_break_in_title"
        ),
        pytest.param("  Prekė  ", "Prekė", id="strips_surrounding_whitespace"),
    ],
)
def test_cell_cleans_text(text, expected):
    assert cell(text) == expected


def test_lines_none_becomes_no_lines():
    assert lines(None) == ()


def test_lines_keeps_line_breaks_and_cleans_each_line():
    assert lines(" Milk   3,95 A\n2,49 X 0,224 kg ") == (
        "Milk 3,95 A",
        "2,49 X 0,224 kg",
    )


MONEY_PREFIXES = st.sampled_from(["€", "", "-"])
# the receipts' money format, which NOT_MONEY must never generate
MONEY_GRAMMAR = re.compile(r"(€|-)?[0-9]+,[0-9]{2}")
WHOLE = st.integers(min_value=0, max_value=999).map(str)
DECIMALS = st.sampled_from(["0", "7", "00", "05", "16", "99", "123"])
MISREAD_DECIMALS = st.sampled_from(["0", "7", "123"])
# money with one thing wrong: the sign, the decimals or a trailing character
ALMOST_MONEY = st.one_of(
    st.builds(
        "{}{},{}".format, st.sampled_from(["€-", "-€", "€€", "--"]), WHOLE, DECIMALS
    ),
    st.builds(
        "{}{},{}{}".format,
        MONEY_PREFIXES,
        WHOLE,
        DECIMALS,
        st.sampled_from(["x", " ", "€"]),
    ),
    st.builds("{}{},{}".format, MONEY_PREFIXES, WHOLE, MISREAD_DECIMALS),
)
NOT_MONEY = st.one_of(
    st.text(alphabet="€-,.x 0123456789abc", max_size=8), ALMOST_MONEY
).filter(lambda text: MONEY_GRAMMAR.fullmatch(text) is None)
MONEY_TEXT = st.builds("{}{},{:02d}".format, MONEY_PREFIXES, WHOLE, st.integers(0, 99))
# an amount that is not "0": fractional pieces, an unknown unit, no unit, no number
UNREADABLE_AMOUNT = st.one_of(
    st.builds(
        "{},{} vnt.".format,
        WHOLE,
        st.text(alphabet="0123456789", min_size=1, max_size=3),
    ),
    st.builds(
        "{} {}{}".format,
        WHOLE,
        st.sampled_from(["pcs", "m", "l", "g"]),
        st.sampled_from(["", "."]),
    ),
    st.text(alphabet="0123456789,", max_size=5).filter(lambda text: text != "0"),
    st.text(alphabet="abc .", max_size=6),
)
PIECES = st.integers(min_value=1, max_value=10**4).map(
    lambda count: (f"{count} vnt.", count)
)
WEIGHT = st.tuples(
    st.integers(min_value=0, max_value=10**4),
    st.text(alphabet="0123456789", min_size=1, max_size=3),
).map(lambda number: (f"{number[0]},{number[1]} kg", 1))


@given(cents=st.integers(min_value=0, max_value=10**7), prefix=MONEY_PREFIXES)
@example(cents=280, prefix="€")
@example(cents=7135, prefix="€")
@example(cents=40, prefix="€")
@example(cents=599, prefix="€")
@example(cents=395, prefix="")
@example(cents=16, prefix="-")
@example(cents=106, prefix="-")
def test_money_reads_back_the_cents_it_was_written_as(cents, prefix):
    expected = cents
    if prefix == "-":
        expected = -cents

    assert money(f"{prefix}{cents // 100},{cents % 100:02d}") == expected


@given(text=NOT_MONEY)
@example(text="")
@example(text="abc")
@example(text="€")
@example(text="€2,8x")
@example(text="3.95")
@example(text="3,9")
@example(text="-€0,16")
@example(text="€-0,16")
def test_money_raises_on_text_that_is_not_money(text):
    with pytest.raises(UnreadableReceiptTextError):
        money(text)


@given(case=st.one_of(PIECES, WEIGHT))
@example(case=("6 vnt.", 6))
@example(case=("1 vnt.", 1))
@example(case=("2 vnt.", 2))
@example(case=("0,404 kg", 1))
@example(case=("1,892 kg", 1))
@example(case=("0,26 kg", 1))
def test_amount_reads_pieces_and_weight(case):
    text, expected = case

    assert amount(text, DEFAULT_UNIT_WORDS) == expected


@given(text=UNREADABLE_AMOUNT)
@example(text="1,5 vnt.")
@example(text="3 pcs")
@example(text="")
@example(text="abc")
@example(text="0,0")
@example(text="00")
def test_amount_raises_on_unreadable_text(text):
    with pytest.raises(UnreadableReceiptTextError):
        amount(text, DEFAULT_UNIT_WORDS)


@pytest.mark.parametrize(
    "text,expected",
    [
        pytest.param("0", 0, id="bare_zero_is_not_collected"),
        pytest.param("0 vnt.", 0, id="zero_pieces"),
        pytest.param("0 kg", 1, id="zero_weight_reads_as_one_as_today"),
    ],
)
def test_amount_reads_zero(text, expected):
    assert amount(text, DEFAULT_UNIT_WORDS) == expected


@pytest.mark.parametrize(
    "title,expected",
    [
        pytest.param(
            "Skardinė (depozitinė) 0,10 EUR, 1 vnt. (UŽSTATAS)", True, id="can"
        ),
        pytest.param("PET (depozitinis) 0,10 EUR, 1 vnt. (UŽSTATAS)", True, id="pet"),
        pytest.param("Bananai, nuo 20 cm, 1 kg", False, id="ordinary_line"),
    ],
)
def test_is_deposit(title, expected):
    assert is_deposit(title, ("UŽSTATAS",)) is expected


@given(
    case=st.one_of(
        MONEY_TEXT.map(lambda text: (text, True)),
        NOT_MONEY.map(lambda text: (text, False)),
    )
)
@example(case=("2,49", True))
@example(case=("€2,49", True))
@example(case=("-0,16", True))
@example(case=("Pack 3", False))
@example(case=("3", False))
@example(case=("", False))
def test_is_money(case):
    text, expected = case

    assert is_money(text) is expected
