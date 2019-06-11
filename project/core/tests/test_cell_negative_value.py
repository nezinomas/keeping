import pytest
from ..templatetags.cell_format import negative


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
