import pytest
import mock

from ..lib.views_helpers import expense_types


@mock.patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects')
def test_expenses_types_no_args(qs):
    qs.all.return_value.values_list.return_value = ['T']

    actual = expense_types()

    assert ['T'] == actual


@mock.patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects')
def test_expenses_types(qs):
    qs.all.return_value.values_list.return_value = ['T']

    actual = expense_types('A')

    assert ['A', 'T'] == actual
