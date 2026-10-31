from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.money_cells import NOTHING, share


@st.composite
def cents_of_a_total(draw):
    total = draw(st.integers(min_value=0, max_value=10**9))

    return draw(st.integers(min_value=0, max_value=total)), total


@given(cents_of_a_total())
@example((0, 0))
@example((500, 0))
@example((1, 100_000))
@example((499, 100_000))
@example((500, 100_000))
@example((99_499, 100_000))
@example((99_500, 100_000))
@example((99_999, 100_000))
@example((100_000, 100_000))
def test_a_share_rounds_to_nothing_or_the_whole_only_when_it_is(cents_and_total):
    cents, total = cents_and_total
    percent = cents / total * 100 if total else 0.0

    actual = share(cents, total)

    if not cents or not total:
        assert actual == NOTHING
    elif cents == total:
        assert actual == "100%"
    elif percent < 0.5:
        assert actual == "< 1%"
    elif percent >= 99.5:
        assert actual == "> 99%"
    else:
        rounded = int(actual.removesuffix("%"))
        assert 1 <= rounded <= 99
        assert abs(rounded - percent) <= 0.5
