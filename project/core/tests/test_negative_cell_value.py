import pytest
from ..templatetags.negative_cell_value import negativecell


def test_value_positive_str():
    actual = negativecell('12.2')

    assert not actual


def test_value_positive_float():
    actual = negativecell(12.2)

    assert not actual


def test_value_positive_int():
    actual = negativecell(12)

    assert not actual


def test_value_negative_str():
    actual = negativecell('-12.2')

    assert actual == 'table-danger'


def test_value_negative_float():
    actual = negativecell(-12.2)

    assert actual == 'table-danger'


def test_value_negative_int():
    actual = negativecell(-12)

    assert actual == 'table-danger'
