import pytest
from mock import patch

from ..lib import views_helpers as T


@patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects')
def test_expenses_types_no_args(qs):
    qs.all.return_value.values_list.return_value = ['T']

    actual = T.expense_types()

    assert ['T'] == actual


@patch('project.bookkeeping.lib.views_helpers.ExpenseType.objects')
def test_expenses_types(qs):
    qs.all.return_value.values_list.return_value = ['T']

    actual = T.expense_types('A')

    assert ['A', 'T'] == actual


@patch('project.bookkeeping.lib.views_helpers.SavingBalance.objects.items')
def test_split_savings_stats(qs):
    qs.return_value = [{'title': 'X'}, {'title': 'Pensija'}]

    fund, pension = T.split_savings_stats(1999)

    assert 'X' == fund[0]['title']
    assert 'Pensija' == pension[0]['title']


@patch('project.bookkeeping.lib.views_helpers.SavingBalance.objects.items')
def test_split_savings_stats_no_pension(qs):
    qs.return_value = [{'title': 'X'}]

    fund, pension = T.split_savings_stats(1999)

    assert 'X' == fund[0]['title']
    assert [] == pension


@patch('project.bookkeeping.lib.views_helpers.SavingBalance.objects.items')
def test_split_savings_stats_no_fund(qs):
    qs.return_value = [{'title': 'X'}]

    fund, pension = T.split_savings_stats(1999)

    assert [] == fund
    assert 'Pensija' == pension[0]['title']


@patch('project.bookkeeping.lib.views_helpers.SavingBalance.objects.items')
def test_split_savings_stats_no_fund(qs):
    qs.return_value = [{'title': 'pensija'}]

    fund, pension = T.split_savings_stats(1999)

    assert [] == fund
    assert 'pensija' == pension[0]['title']


@patch('project.bookkeeping.lib.views_helpers.SavingBalance.objects.items')
def test_split_savings_stats_empty_queryset(qs):
    qs.return_value = []

    fund, pension = T.split_savings_stats(1999)

    assert [] == fund
    assert [] == pension
