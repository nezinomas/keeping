from datetime import date
from decimal import Decimal

import pytest
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

    actual = T.split_funds(lst, 'lx')

    assert 1 == len(actual)
    assert 'AAA LX' == actual[0]['title']


@pytest.fixture
def _income():
    return [
        {'date': date(1999, 1, 1), 'title': 'A', 'sum': Decimal(1)},
        {'date': date(1999, 1, 1), 'title': 'A', 'sum': Decimal(4)},
        {'date': date(1999, 6, 1), 'title': 'B', 'sum': Decimal(2)},
    ]


def test_sum_detailed(_income):
    expect = [
        {'date': date(1999, 1, 1), 'sum': Decimal(5)},
        {'date': date(1999, 6, 1), 'sum': Decimal(2)},
    ]
    actual = T.sum_detailed(_income)

    assert expect == actual
