import pytest
from ..templatetags import math

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


@pytest.mark.parametrize(
    'a, b, expect',
    [
        (1, -1, 2),
        (-1, 1, -2),
        (1, 1, 0),
    ]
)
def test_sub(a, b, expect):
    actual = math.sub(a, b)
    assert actual == expect


@pytest.mark.parametrize(
    'a, b, expect',
    [
        (10, 1, 10),
        (1, 10, 1_000),
    ]
)
def test_percent(a, b, expect):
    actual = math.percent(a, b)
    assert actual == expect
