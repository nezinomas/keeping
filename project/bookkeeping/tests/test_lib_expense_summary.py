from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from ...core.lib.balance_base import df_months_of_year
from ..lib.expense_balance import ExpenseBalance


@pytest.fixture
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


@pytest.fixture
def _types():
    return ['T1', 'T2']


def test_expenes_and_exceptions_same_size(_expenses, _types):
    df = df_months_of_year(1999)

    actual = ExpenseBalance(df, _expenses, _types)

    assert actual.exceptions.shape[0] == actual.expenses.shape[0]


def test_exceptions(_expenses, _types):
    df = df_months_of_year(1999)

    actual = ExpenseBalance(df, _expenses, _types).exceptions

    assert isinstance(actual, pd.DataFrame)
    assert actual.loc['1999-1-1', 'sum'] == 1.0


def test_expenses(_expenses, _types):
    df = df_months_of_year(1999)

    actual = ExpenseBalance(df, _expenses, _types).expenses

    assert isinstance(actual, pd.DataFrame)

    assert actual.loc['1999-01-01', 'T1'] == 0.25
    assert actual.loc['1999-01-01', 'T2'] == 0.5

    assert actual.loc['1999-12-01', 'T1'] == 0.75
    assert actual.loc['1999-12-01', 'T2'] == 0.35


def test_types_no_data():
    df = df_months_of_year(1999)

    actual = ExpenseBalance(df, [], []).types

    assert isinstance(actual, list)
    assert len(actual) == 0


def test_types_with_data(_types):
    df = df_months_of_year(1999)

    actual = ExpenseBalance(df, [], _types).types

    assert isinstance(actual, list)
    assert actual == _types


def test_types(_expenses, _types):
    df = df_months_of_year(1999)

    _expenses.append({
        'date': date(1999, 1, 1),
        'title': 'AAA',
        'sum': Decimal(0.25),
        'exception_sum': Decimal(1.0)
    })

    actual = ExpenseBalance(df, _expenses, _types).types

    assert actual == ['AAA', 'T1', 'T2']
