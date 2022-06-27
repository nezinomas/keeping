from datetime import date
from decimal import Decimal

import pandas as pd
from mock import patch

from ..services.expenses import ExpensesService


def _expenses():
    return ([
        {
            'date': date(1999, 1, 1),
            'title': 'T1',
            'sum': Decimal(0.25),
            'exception_sum': Decimal(1.0)
        }, {
            'date': date(1999, 1, 1),
            'title': 'T2',
            'sum': Decimal(0.5),
            'exception_sum': Decimal(0)
        }, {
            'date': date(1999, 12, 1),
            'title': 'T1',
            'sum': Decimal(0.75),
            'exception_sum': Decimal(0)
        }, {
            'date': date(1999, 12, 1),
            'title': 'T2',
            'sum': Decimal(0.35),
            'exception_sum': Decimal(0)
        },
    ])


@patch('project.expenses.models.Expense.objects.sum_by_month_and_type', return_value=_expenses())
def test_balance(mck, rf):
    expect = [
        {'date': pd.Timestamp(1999, 1, 1), 'T1': 0.25, 'T2': 0.5},
        {'date': pd.Timestamp(1999, 2, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 3, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 4, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 5, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 6, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 7, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 8, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 9, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 10, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 11, 1), 'T1': 0.0, 'T2': 0.0},
        {'date': pd.Timestamp(1999, 12, 1), 'T1': 0.75, 'T2': 0.35},
    ]

    actual = ExpensesService(request=rf, year=1999)._balance

    assert expect == actual


@patch('project.expenses.models.Expense.objects.sum_by_month_and_type', return_value=_expenses())
def test_total_row(mck, rf):
    expect = {'T1': 1.0, 'T2': 0.85}

    actual = ExpensesService(request=rf, year=1999)._total_row

    assert expect == actual


@patch('project.expenses.models.Expense.objects.sum_by_month_and_type', return_value=_expenses())
def test_average(mck, rf):
    expect = {'T1': 0.5, 'T2': 0.425}

    actual = ExpensesService(request=rf, year=1999)._average

    assert expect == actual


@patch('project.expenses.models.Expense.objects.sum_by_month_and_type', return_value=_expenses())
def test_chart_data(mck, rf):
    expect = [
        {'name': 'T1', 'y': 1.0},
        {'name': 'T2', 'y': 0.85}
    ]

    actual = ExpensesService(request=rf, year=1999)._chart_data()

    assert expect == actual


@patch('project.expenses.models.Expense.objects.sum_by_month_and_type', return_value={})
@patch('project.bookkeeping.services.expenses.expense_types', return_value=None)
def test_chart_data_none(mck_qs, mck_types, rf):
    expect = [{'name': 'Išlaidų nėra', 'y': 0}]

    actual = ExpensesService(request=rf, year=1999)._chart_data()

    assert expect == actual


@patch('project.expenses.models.Expense.objects.sum_by_month_and_type', return_value={})
@patch('project.bookkeeping.services.expenses.expense_types', return_value=[])
def test_chart_data_empty(mck_qs, mck_types, rf):
    expect = [{'name': 'Išlaidų nėra', 'y': 0}]

    actual = ExpensesService(request=rf, year=1999)._chart_data()

    assert expect == actual
