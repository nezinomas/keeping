import pytest

from ..templatetags import template_filters as T


def test_cellformat_int():
    expect = '1,00'

    actual = T.cellformat(1)

    assert expect == actual


def test_cellformat_float():
    expect = '1,00'

    actual = T.cellformat(1.0)

    assert expect == actual


def test_cellformat_str_dot():
    expect = '1,00'

    actual = T.cellformat('1.0')

    assert expect == actual


def test_cellformat_str():
    expect = 'xx'

    actual = T.cellformat('xx')

    assert expect == actual


def test_cellformat_none():
    expect = '-'

    actual = T.cellformat(None)

    assert expect == actual


def test_cellformat_long_float():
    expect = '1,01'

    actual = T.cellformat(1.0111)

    assert expect == actual


def test_cellformat_float_zero():
    expect = '-'

    actual = T.cellformat(0.0)

    assert expect == actual


def test_cellformat_int_zero():
    expect = '-'

    actual = T.cellformat(0)

    assert expect == actual


def test_cellformat_str_zero():
    expect = '-'

    actual = T.cellformat('0')

    assert expect == actual


@pytest.mark.parametrize(
    'dictionary, key, expect',
    [
        ({'x': 'val'}, 'x', 'val'),
        ({'x': 'val'}, 'y', 0.0),
        (None, 'y', None),
        ({}, 'y', None),
    ]
)
def test_get_item(dictionary, key, expect):
    assert T.get_item(dictionary, key) == expect


@pytest.mark.parametrize(
    'value, css_class, expect',
    [
        ('0', 'X', 'X'),
        (0, 'X', 'X'),
        ('6', 'X', 'X'),
        (6, 'X', 'X'),
        ('1', 'X', None),
        (1, 'X', None),
    ])
def test_weekend(value, css_class, expect):
    assert T.weekend(value, css_class) == expect
