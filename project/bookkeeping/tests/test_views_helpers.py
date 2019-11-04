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
