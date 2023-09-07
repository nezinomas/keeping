import pytest
from hypothesis import given, assume
from hypothesis import strategies as st

from ..templatetags import math


@st.composite
def numbers_strategy(draw):
    return draw(st.none() | st.integers() | st.floats(allow_nan=False, allow_infinity=False))


@pytest.mark.parametrize(
    'value, expect',
    [
        (1, 0.01),
        (.1, 0.001),
        (None, None),
        ('-', '-'),
    ]
)
def test_price(value, expect):
    actual = math.price(value)
    assert actual == expect


@given(numbers_strategy(), numbers_strategy())
def test_sub(x, y):
    if x is None or y is None:
        assert math.sub(x, y) == 0

    assume(x and y)
    assert math.sub(x, y) == x - y


@pytest.mark.parametrize(
    'a, b, expect',
    [
        (10, 1, 10),
        (1, 10, 1_000),
        (0, 1, 0),
        (1, 0, 0),
        (1, None, 0),
        (None, 0, 0),
        (None, None, 0),
    ]
)
def test_percent(a, b, expect):
    actual = math.percent(a, b)
    assert actual == expect
