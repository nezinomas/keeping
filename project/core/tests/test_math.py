import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from ..templatetags import math


numbers_strategy = st.one_of(
    st.integers(min_value=0),
    st.floats(min_value=0, allow_nan=False, allow_infinity=False, width=16),
)


@pytest.mark.parametrize(
    "value, expect",
    [
        (1, 0.01),
        (0.1, 0.001),
        (None, None),
        ("-", "-"),
    ],
)
def test_price(value, expect):
    actual = math.price(value)
    assert actual == expect


@given(numbers_strategy)
def test_sub_type_error(num):
    assert math.sub(num, None) == 0
    assert math.sub(None, num) == 0


@given(numbers_strategy, numbers_strategy)
def test_sub_commutative(x, y):
    assert math.sub(x, y) == -(math.sub(y, x))


@given(numbers_strategy)
def test_percent_type_error(num):
    assert math.percent(num, None) == 0
    assert math.percent(None, num) == 0


@given(numbers_strategy)
def test_percent_zero_division(num):
    assert math.percent(num, 0) == 0


@given(numbers_strategy, numbers_strategy)
def test_percent_proportion(a, b):
    assume(a and b)
    left = b / a
    right = math.percent(a, b) / 100
    assert pytest.approx(left) == pytest.approx(right)


def test_percent_unit_test():
    assert math.percent(75, 15) == 20
