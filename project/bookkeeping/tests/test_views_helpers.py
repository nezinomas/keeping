from datetime import date
from decimal import Decimal

import pytest
from freezegun import freeze_time
from mock import patch

from ..lib import views_helpers as T


@patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects.items')
def test_expenses_types_no_args(qs):
    qs.return_value.values_list.return_value = ['T']

    actual = T.expense_types()

    assert ['T'] == actual


@patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects.items')
def test_expenses_types(qs):
    qs.return_value.values_list.return_value = ['T']

    actual = T.expense_types('A')

    assert ['A', 'T'] == actual


def test_split_funds():
    lst = [{'title': 'AAA LX'}, {'title': 'INVL'}]

    a1, a2 = T.split_funds(lst, 'lx')

    assert a1[0]['title'] == 'AAA LX'
    assert a2[0]['title'] == 'INVL'


@pytest.fixture
def _income():
    return [
        {'date': date(1999, 1, 1), 'title': 'A', 'sum': Decimal(1)},
        {'date': date(1999, 1, 1), 'title': 'A', 'sum': Decimal(4)},
        {'date': date(1999, 6, 1), 'title': 'B', 'sum': Decimal(2)},
    ]


def test_sum_detailed_rows(_income):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5)},
        {'date': date(1999, 6, 1), 'sum': Decimal(2)},
    ]
    actual = T.sum_detailed(_income, 'date', ['sum'])

    assert expect == actual


def test_sum_detailed_columns(_income):
    expect = [
        {'title': 'A', 'sum': Decimal(5)},
        {'title': 'B', 'sum': Decimal(2)},
    ]

    actual = T.sum_detailed(_income, 'title', ['sum'])

    assert expect == actual


def test_percentage_from_incomes():
    actual = T.percentage_from_incomes(10, 1.5)

    assert 15 == actual


def test_percentage_from_incomes_saving_none():
    actual = T.percentage_from_incomes(10, None)

    assert not actual


# ---------------------------------------------------------------------------------------
#                                                                              No Incomes
# ---------------------------------------------------------------------------------------
@pytest.fixture
def _expenses():
    arr = [
        {'date': date(2020, 1, 1), 'sum': Decimal('1.00'), 'title': 'X'},
        {'date': date(2020, 1, 1), 'sum': Decimal('2.60'), 'title': 'Y'},
        {'date': date(2020, 1, 1), 'sum': Decimal('3.00'), 'title': 'Z'},
        # --------------------------------------------------------------
        {'date': date(2020, 6, 1), 'sum': Decimal('4.00'), 'title': 'X'},
        {'date': date(2020, 6, 1), 'sum': Decimal('5.60'), 'title': 'Y'},
        {'date': date(2020, 6, 1), 'sum': Decimal('6.00'), 'title': 'Z'},
        # --------------------------------------------------------------
        {'date': date(2020, 12, 1), 'sum': Decimal('7.00'), 'title': 'X'},
        {'date': date(2020, 12, 1), 'sum': Decimal('8.60'), 'title': 'Y'},
        {'date': date(2020, 12, 1), 'sum': Decimal('9.00'), 'title': 'Z'},
    ]
    return arr


@pytest.fixture
def _savings():
    arr = [
        {'date': date(2020, 1, 1), 'sum': Decimal('2.00')},
        {'date': date(2020, 6, 1), 'sum': Decimal('2.00')},
        {'date': date(2020, 12, 1), 'sum': Decimal('2.00')},
    ]
    return arr


@pytest.fixture
def _not_use():
    return ['Z']


@freeze_time('2020-07-07')
def test_no_incomes_data(_not_use, _expenses, _savings):
    avg_expenses, cut_sum = T.no_incomes_data(not_use=_not_use, expenses=_expenses, savings=_savings)

    assert avg_expenses == pytest.approx(4.37, rel=1e-2)
    assert cut_sum == pytest.approx(2.17, rel=1e-2)


@freeze_time('2020-07-07')
def test_no_incomes_data_not_use_empty(_expenses):
    avg_expenses, cut_sum = T.no_incomes_data(not_use=[], expenses=_expenses)

    assert avg_expenses == pytest.approx(3.69, rel=1e-2)
    assert cut_sum == 0.0


@freeze_time('2020-07-07')
def test_no_incomes_data_not_use_none(_expenses):
    avg_expenses, cut_sum = T.no_incomes_data(not_use=None, expenses=_expenses)

    assert avg_expenses == pytest.approx(3.69, rel=1e-2)
    assert cut_sum == 0.0


@freeze_time('2020-07-07')
def test_no_incomes_data_no_savings(_not_use, _expenses):
    avg_expenses, cut_sum = T.no_incomes_data(not_use=_not_use, expenses=_expenses)

    assert avg_expenses == pytest.approx(3.69, rel=1e-2)
    assert cut_sum == pytest.approx(1.5, rel=1e-2)
