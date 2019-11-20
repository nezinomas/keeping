import pytest

from ..templatetags import template_filters as T


@pytest.mark.parametrize(
    'value, expect',
    [
        (1, '1,00'),
        (1.0, '1,00'),
        ('1,00', '1,00'),
        ('xx', 'xx'),
        (None, '-'),
        (1.0111, '1,01'),
        (1.049, '1,05'),
        (0.0, '-'),
        (0, '-'),
        ('0', '-'),
    ])
def test_cellformat(value, expect):
    assert T.cellformat(value) == expect


@pytest.mark.parametrize(
    'dictionary, key, expect',
    [
        ({'x': 'val'}, 'x', 'val'),
        ({'x': 'val'}, 'y', 0.0),
        (None, 'y', None),
        ({}, 'y', None),
    ])
def test_get_item(dictionary, key, expect):
    assert T.get_item(dictionary, key) == expect


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
