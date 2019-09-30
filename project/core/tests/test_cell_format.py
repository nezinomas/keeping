from decimal import Decimal

import pytest

from ..templatetags.cell_format import (comparison, negative, positive,
                                        positive_negative)


def test_value_positive_str():
    actual = negative('12.2')

    assert not actual


def test_value_positive_float():
    actual = negative(12.2)

    assert not actual


def test_value_positive_int():
    actual = negative(12)

    assert not actual


def test_value_negative_str():
    actual = negative('-12.2')

    assert actual == 'table-danger'


def test_value_negative_float():
    actual = negative(-12.2)

    assert actual == 'table-danger'


def test_value_negative_int():
    actual = negative(-12)

    assert actual == 'table-danger'


def test_value_str():
    actual = negative('xxx')

    assert not actual


# postive custom template filter tests
def test_value_negative_float_1():
    actual = positive(-12.2)

    assert not actual


def test_value_negative_str_1():
    actual = positive('-12.2')

    assert not actual


def test_value_negative_int_1():
    actual = positive(-12)

    assert not actual


def test_value_positive_float_1():
    actual = positive(12.2)

    assert actual == 'table-success'


def test_value_positive_int_1():
    actual = positive(12)

    assert actual == 'table-success'


def test_value_str_1():
    actual = positive('xxx')

    assert not actual


def test_comparison_bigger_str():
    actual = comparison('1', '2')

    assert 'table-success' == actual


def test_comparison_bigger_int():
    actual = comparison(1, 2)

    assert 'table-success' == actual


def test_comparison_smaller_str():
    actual = comparison('1', '0')

    assert 'table-danger' == actual


def test_comparison_smaller_int():
    actual = comparison(1, 0)

    assert 'table-danger' == actual


def test_comparison_smaller_decimal():
    actual = comparison(1, Decimal(0.1))

    assert 'table-danger' == actual


def test_comparison_none():
    actual = comparison(None, None)

    assert not actual


def test_positive_negative_positive():
    actual = positive_negative('1')

    assert 'table-success' == actual


def test_positive_negative_negative():
    actual = positive_negative('-1')

    assert 'table-danger' == actual
