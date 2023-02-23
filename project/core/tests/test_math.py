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
