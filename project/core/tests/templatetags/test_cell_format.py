from hypothesis import example, given
from hypothesis import strategies as st

from ...templatetags.cell_format import cell_state, cellformat, sign


@st.composite
def values_and_signs(draw):
    """Below zero is a loss, zero and up a gain, as a number or its text; anything
    that is no number has no sign."""
    if draw(st.booleans()):
        return draw(st.none() | st.text(alphabet="abcxyz ?!")), ""

    below = st.integers(max_value=-1) | st.floats(max_value=-1e-9, min_value=-1e12)
    from_zero = st.integers(min_value=0) | st.floats(min_value=0, max_value=1e12)
    number, state = draw(
        st.tuples(below, st.just("loss")) | st.tuples(from_zero, st.just("gain"))
    )

    return draw(st.sampled_from([number, str(number)])), state


@given(values_and_signs())
@example((-12, "loss"))
@example((-12.2, "loss"))
@example(("-12.2", "loss"))
@example((0, "gain"))
@example((12, "gain"))
@example((12.2, "gain"))
@example(("12.2", "gain"))
@example(("abc", ""))
@example((None, ""))
def test_sign(case):
    value, state = case

    assert sign(value) == state


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


@st.composite
def values_and_cell_states(draw):
    """An empty or zero value is an empty cell; any other is not."""
    if draw(st.booleans()):
        return draw(st.sampled_from([None, 0, 0.0, "", []])), "empty"

    filled = (
        st.integers().filter(bool)
        | st.floats().filter(bool)
        | st.text(min_size=1)
        | st.lists(st.integers(), min_size=1)
    )
    return draw(filled), ""


@given(values_and_cell_states())
@example((None, "empty"))
@example((0, "empty"))
@example((0.0, "empty"))
@example(("", "empty"))
@example(([], "empty"))
@example((1, ""))
@example((-1, ""))
@example((0.5, ""))
@example(("abc", ""))
def test_cell_state(case):
    value, state = case

    assert cell_state(value) == state
