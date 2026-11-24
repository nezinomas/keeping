from hypothesis import given
from hypothesis import strategies as st

from ...templatetags import math

numbers_strategy = st.one_of(
    st.integers(min_value=0),
    st.floats(min_value=0, allow_nan=False, allow_infinity=False, width=16),
)


def test_price_not_a_number():
    assert math.price("-") == "-"


@given(st.integers(min_value=1))
def test_price(num):
    assert math.price(num) == num / 100


@given(numbers_strategy)
def test_sub_type_error(num):
    assert math.sub(num, None) == 0
    assert math.sub(None, num) == 0


@given(numbers_strategy, numbers_strategy)
def test_sub_commutative(x, y):
    assert math.sub(x, y) == -(math.sub(y, x))
