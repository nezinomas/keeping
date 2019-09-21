import pytest

from ..templatetags.template_filters import cellformat, get_item


def test_cellformat_int():
    expect = '1,00'

    actual = cellformat(1)

    assert expect == actual


def test_cellformat_float():
    expect = '1,00'

    actual = cellformat(1.0)

    assert expect == actual


def test_cellformat_str_dot():
    expect = '1,00'

    actual = cellformat('1.0')

    assert expect == actual


def test_cellformat_str():
    expect = 'xx'

    actual = cellformat('xx')

    assert expect == actual


def test_cellformat_none():
    expect = '-'

    actual = cellformat(None)

    assert expect == actual


def test_cellformat_long_float():
    expect = '1,01'

    actual = cellformat(1.0111)

    assert expect == actual


def test_cellformat_float_zero():
    expect = '-'

    actual = cellformat(0.0)

    assert expect == actual


def test_cellformat_int_zero():
    expect = '-'

    actual = cellformat(0)

    assert expect == actual


def test_cellformat_str_zero():
    expect = '-'

    actual = cellformat('0')

    assert expect == actual


def test_get_item():
    expect = 'val'

    actual = get_item({'x': 'val'}, 'x')

    assert expect == actual


def test_get_item_wrong_key():
    expect = 0.0

    actual = get_item({'x': 'val'}, 'y')

    assert expect == actual


def test_get_item_dictionary_none():
    expect = None

    actual = get_item(None, 'y')

    assert expect == actual
