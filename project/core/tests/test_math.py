import pytest
from hypothesis import assume, example, given
from hypothesis import strategies as st

from ..templatetags import math

numbers_strategy = st.one_of(st.floats(allow_nan=False, allow_infinity=False), st.integers())


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


@given(numbers_strategy, numbers_strategy)
@example(None, None)
def test_sub(x, y):
    if x is None or y is None:
        assert math.sub(x, y) == 0

    assume(x and y)
    assert math.sub(x, y) == x - y


@given(numbers_strategy, numbers_strategy)
@example(None, None)
def test_percent(a, b):
    if a is None or b is None:
        assert math.percent(a, b) == 0

    if a == 0:
        assert math.percent(a, b) == 0

    assume(a and b)
    assert math.percent(a, b) == (b / a) * 100
