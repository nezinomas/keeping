import pytest

from ..templatetags.decimal_format import decimalformat


def test_no_value():
    actual = decimalformat(None)

    assert '-' == actual


def test_value_str():
    actual = decimalformat('str')

    assert '-' == actual


def test_round_float_1():
    actual = decimalformat(1.123)

    assert str(1.12) == actual


def test_round_float_2():
    actual = decimalformat(1.126)

    assert str(1.13) == actual


def test_round_float_3():
    actual = decimalformat('1.123')

    assert str(1.12) == actual


def test_incoma():
    actual = decimalformat(1000)

    assert '1,000.00' == actual
