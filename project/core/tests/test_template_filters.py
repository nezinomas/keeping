import pytest

from ..templatetags.template_filters import cellformat as T


def test_cellformat_int():
    expect = '1,00'

    actual = T(1)

    assert expect == actual


def test_cellformat_float():
    expect = '1,00'

    actual = T(1.0)

    assert expect == actual


def test_cellformat_str_dot():
    expect = '1,00'

    actual = T('1.0')

    assert expect == actual


def test_cellformat_str():
    expect = 'xx'

    actual = T('xx')

    assert expect == actual


def test_cellformat_none():
    expect = None

    actual = T(None)

    assert expect == actual


def test_cellformat_long_float():
    expect = '1,01'

    actual = T(1.0111)

    assert expect == actual


def test_cellformat_float_zero():
    expect = '-'

    actual = T(0.0)

    assert expect == actual


def test_cellformat_int_zero():
    expect = '-'

    actual = T(0)

    assert expect == actual


def test_cellformat_str_zero():
    expect = '-'

    actual = T('0')

    assert expect == actual
