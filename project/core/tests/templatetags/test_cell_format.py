import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...templatetags.cell_format import cell_state, cellformat, sign


@pytest.mark.parametrize(
    "value, expect",
    [
        (-12, "loss"),
        (-12.2, "loss"),
        ("-12.2", "loss"),
        (0, "gain"),
        (12, "gain"),
        (12.2, "gain"),
        ("12.2", "gain"),
        ("abc", ""),
        (None, ""),
    ],
)
def test_sign(value, expect):
    actual = sign(value)

    assert actual == expect


def lt_money(cents: int) -> str:
    whole, part = divmod(abs(cents), 100)
    minus = "-" * (cents < 0)

    return f"{minus}{whole:,}".replace(",", ".") + f",{part:02d}"


@st.composite
def cellformat_cases(draw):
    default = draw(st.text(max_size=5))
    if draw(st.booleans()):
        return draw(st.none() | st.text(alphabet="xyzXYZ !?-")), default, default

    cents = draw(st.integers(-2, 2) | st.integers(-(10**11), 10**11))
    noise = draw(st.floats(min_value=-0.4, max_value=0.4))
    number = (cents + noise) / 100
    forms = {
        "float": number,
        "string": repr(number),
        "comma": repr(number).replace(".", ","),
    }
    if cents % 100 == 0:
        forms["int"] = cents // 100

    expect = default if cents == 0 else lt_money(cents)

    return forms[draw(st.sampled_from(sorted(forms)))], default, expect


@given(cellformat_cases())
@example((0, "-", "-"))
@example((0.0, "-", "-"))
@example(("0", "-", "-"))
@example(("0.0", "-", "-"))
@example(("0,0", "-", "-"))
@example(("0.00", "-", "-"))
@example(("0,00", "-", "-"))
@example((-0.0001, "-", "-"))
@example(("-0.0001", "-", "-"))
@example((1, "-", "1,00"))
@example((1.0, "-", "1,00"))
@example(("1.00", "-", "1,00"))
@example(("1,00", "-", "1,00"))
@example((1.0111, "-", "1,01"))
@example((1.049, "-", "1,05"))
@example((-0.5, "-", "-0,50"))
@example(("-0.5", "-", "-0,50"))
@example(("-0,5", "-", "-0,50"))
@example((None, "-", "-"))
@example((None, "ok", "ok"))
@example(("None", "ok", "ok"))
@example(("xx", "-", "-"))
@example((1000, "-", "1.000,00"))
@example(("1000", "-", "1.000,00"))
def test_cellformat(case):
    value, default, expect = case

    assert cellformat(value, default) == expect


@pytest.mark.parametrize(
    "value, expect",
    [
        (None, "empty"),
        (0, "empty"),
        (0.0, "empty"),
        ("", "empty"),
        ([], "empty"),
        (1, ""),
        (-1, ""),
        (0.5, ""),
        ("abc", ""),
    ],
)
def test_cell_state(value, expect):
    assert cell_state(value) == expect
