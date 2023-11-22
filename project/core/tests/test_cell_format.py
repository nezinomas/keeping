import pytest

from ..templatetags.cell_format import (cellformat, compare, negative,
                                        positive, positive_negative)


@pytest.mark.parametrize(
    'value, expect',
    [
        (0, ''),
        (12, ''),
        (12.2, ''),
        ('12.2', ''),
        ('xxx', ''),
        (-0, ''),
        (-12, 'table-danger'),
        (-12.2, 'table-danger'),
        ('-12.2', 'table-danger'),
    ]
)
def test_negative(value, expect):
    actual = negative(value)

    assert actual == expect


@pytest.mark.parametrize(
    'value, expect',
    [
        (-12, ''),
        (-12.2, ''),
        ('-12.2', ''),
        ('xxx', ''),
        (0, 'table-success'),
        (12, 'table-success'),
        (12.2, 'table-success'),
        ('12.2', 'table-success'),
    ]
)
# postive custom template filter tests
def test_positive(value, expect):
    actual = positive(value)

    assert actual == expect


@pytest.mark.parametrize(
    'value1, value2, expect',
    [
        (1, 2, 'table-danger'),
        ('1', '2', 'table-danger'),
        (1, 0, 'table-success'),
        ('1', '0', 'table-success'),
        (None, None, ''),
        ('x', 1, ''),
        (1, 'x', ''),
    ]
)
def test_compare(value1, value2, expect):
    actual = compare(value1, value2)

    assert actual == expect


@pytest.mark.parametrize(
    'value, expect',
    [
        (1, 'table-success'),
        ('1', 'table-success'),
        (-1, 'table-danger'),
        ('-1', 'table-danger'),
        ('x', ''),
    ]
)
def test_positive_negative_positive(value, expect):
    actual = positive_negative(value)

    assert actual == expect


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
