from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from ..lib.expense_type_stats import MonthExpenseType, MonthsExpenseType


@pytest.fixture
def _ex():
    return ([
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'T1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(0.25), 'title': 'T2'},
        {'date': date(1999, 12, 1), 'sum': Decimal(0.75), 'title': 'T1'},
        {'date': date(1999, 12, 1), 'sum': Decimal(0.35), 'title': 'T2'},
    ])


@pytest.fixture()
def _savings():
    return ({
        'X': [
            {'date': date(1999, 1, 1), 'sum': Decimal(0.5)},
        ]
    })


def test_month_balance_lenght_empty_expenses():
    actual = MonthExpenseType(1999, 1, []).balance

    assert 31 == len(actual)


def test_month_balance_lenght_none_expenses():
    actual = MonthExpenseType(1999, 1, None).balance

    assert 31 == len(actual)


def test_month_balance_january(_ex):
    expect = {'date': date(1999, 1, 1), 'T1': 0.5, 'T2': 0.25, 'total': 0.75}

    actual = MonthExpenseType(year=1999, month=1, expenses=_ex[:2]).balance

    assert expect == actual[0]


def test_months_expense_type(_ex):
    expect = [
        {'date': date(1999, 1, 1), 'T1': 0.5, 'T2': 0.25, 'total': 0.75},
        {'date': date(1999, 2, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 3, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 4, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 5, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 6, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 7, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 8, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 9, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 10, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 11, 1), 'T1': 0.0, 'T2': 0.0, 'total': 0.0},
        {'date': date(1999, 12, 1), 'T1': 0.75, 'T2': 0.35, 'total': 1.1},
    ]

    actual = MonthsExpenseType(1999, _ex).balance

    assert expect == actual


def test_months_expense_type_totals(_ex):
    expect = {'T1': 1.25, 'T2': 0.6, 'total': 1.85}

    actual = MonthsExpenseType(1999, _ex).totals

    assert expect == actual


def test_months_expense_type_average(_ex):
    expect = {'T1': 0.625, 'T2': 0.3, 'total': 0.925}

    actual = MonthsExpenseType(1999, _ex).average

    assert expect == actual


def test_months_expense_chart_data(_ex):
    expect = [
        {'name': 'T1', 'y': 1.25},
        {'name': 'T2', 'y': 0.6}
    ]

    actual = MonthsExpenseType(1999, _ex).chart_data

    assert expect == actual


def test_months_expense_chart_data_none():
    expect = []

    actual = MonthsExpenseType(1999, None).chart_data

    assert expect == actual


def test_months_expense_chart_data_empty():
    expect = []

    actual = MonthsExpenseType(1999, []).chart_data

    assert expect == actual


def test_month_with_savings(_ex, _savings):
    expect = {'date': date(1999, 1, 1), 'T1': 0.5, 'T2': 0.25, 'X': 0.5, 'total': 1.25}

    actual = MonthExpenseType(year=1999, month=1, expenses=_ex[:2], **_savings).balance

    assert expect == actual[0]


def test_months_with_savings(_ex, _savings):
    expect = {'date': date(1999, 1, 1), 'T1': 0.5, 'T2': 0.25, 'X': 0.5, 'total': 1.25}

    actual = MonthsExpenseType(year=1999, expenses=_ex, **_savings).balance

    assert expect == actual[0]


def test_month_return_dataframe(_ex):
    actual = MonthExpenseType(year=1999, month=1, expenses=_ex[:2]).balance_df

    assert isinstance(actual, pd.DataFrame)
    assert 31 == len(actual)
