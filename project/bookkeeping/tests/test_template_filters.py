import pytest

from ..templatetags import template_filters as T


@pytest.mark.parametrize(
    'value, css_class, expect',
    [
        ('0', 'X', 'X'), # saturday
        (0, 'X', 'X'), # saturday
        ('6', 'X', 'X'), # sunday
        (6, 'X', 'X'), # sunday
        ('1', 'X', ''),
        (1, 'X', ''),
    ])
def test_weekend(value, css_class, expect):
    assert T.weekend(value, css_class) == expect
