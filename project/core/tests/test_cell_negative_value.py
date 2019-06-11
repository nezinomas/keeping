import pytest
from ..templatetags.cell_format import negative, positive


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
