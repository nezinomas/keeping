import pytest

from ..templatetags.cell_format import (cellformat, compare, negative,
                                        positive, positive_negative)


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


def test_compare_bigger_str():
    actual = compare('1', '2')

    assert actual == 'table-danger'


def test_compare_bigger_int():
    actual = compare(1, 2)

    assert actual == 'table-danger'


def test_compare_smaller_str():
    actual = compare('1', '0')

    assert actual == 'table-success'


def test_compare_smaller_int():
    actual = compare(1, 0)

    assert actual == 'table-success'


def test_compare_none():
    actual = compare(None, None)

    assert not actual


def test_positive_negative_positive():
    actual = positive_negative('1')

    assert actual == 'table-success'


def test_positive_negative_negative():
    actual = positive_negative('-1')

    assert actual == 'table-danger'


@pytest.mark.parametrize(
    'value, default, expect',
    [
        (0, '-', '-'),
        (0.0, '-', '-'),
        ('0', '-', '-'),
        ('0.0', '-', '-'),
        ('0,0', '-', '-'),
        ('0.00', '-', '-'),
        ('0,00', '-', '-'),
        (-0.0001, '-', '-'),
        ('-0.0001', '-', '-'),
        (1, '-', '1,00'),
        (1.0, '-', '1,00'),
        ('1.00', '-', '1,00'),
        ('1,00', '-', '1,00'),
        (1.0111, '-', '1,01'),
        (1.049, '-', '1,05'),
        (-0.5, '-', '-0,50'),
        ('-0.5', '-', '-0,50'),
        ('-0,5', '-', '-0,50'),
        (None, '-', '-'),
        (None, 'ok', 'ok'),
        ('None', 'ok', 'ok'),
        ('xx', '-', 'xx'),
    ])
def test_cellformat(value, default, expect):
    assert cellformat(value, default) == expect
