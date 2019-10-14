from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from ..lib.expense_stats import MonthExpenseType, MonthsExpenseType


@pytest.fixture
def _ex():
    return ([
        {'date': date(1999, 1, 1), 'sum': Decimal(0.25), 'title': 'T1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'T2'},
        {'date': date(1999, 12, 1), 'sum': Decimal(0.75), 'title': 'T1'},
        {'date': date(1999, 12, 1), 'sum': Decimal(0.35), 'title': 'T2'},
    ])


@pytest.fixture
def _ex_targets():
    return (
        {'T1': Decimal(0.3), 'T2': Decimal(0.4)}
    )


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
    expect = {'date': date(1999, 1, 1), 'T1': 0.25, 'T2': 0.5, 'total': 0.75}

    actual = MonthExpenseType(year=1999, month=1, expenses=_ex[:2]).balance

    assert expect == actual[0]


def test_months_expense_type(_ex):
    expect = [
        {'date': date(1999, 1, 1), 'T1': 0.25, 'T2': 0.5, 'total': 0.75},
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
    expect = {'T1': 1.0, 'T2': 0.85, 'total': 1.85}

    actual = MonthsExpenseType(1999, _ex).totals

    assert expect == actual


def test_months_expense_type_average(_ex):
    expect = {'T1': 0.5, 'T2': 0.425, 'total': 0.925}

    actual = MonthsExpenseType(1999, _ex).average

    assert expect == actual


def test_months_expense_chart_data(_ex):
    expect = [
        {'name': 'T1', 'y': 1.0},
        {'name': 'T2', 'y': 0.85}
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
    expect = {'date': date(1999, 1, 1), 'T1': 0.25, 'T2': 0.5, 'X': 0.5, 'total': 1.25}

    actual = MonthExpenseType(year=1999, month=1, expenses=_ex[:2], **_savings).balance

    assert expect == actual[0]


def test_month_with_only_savings(_savings):
    expect = {'date': date(1999, 1, 1), 'X': 0.5, 'total': 0.5}

    actual = MonthExpenseType(year=1999, month=1, expenses=[], **_savings).balance

    assert expect == actual[0]


def test_months_with_savings(_ex, _savings):
    expect = {'date': date(1999, 1, 1), 'T1': 0.25, 'T2': 0.5, 'X': 0.5, 'total': 1.25}

    actual = MonthsExpenseType(year=1999, expenses=_ex, **_savings).balance

    assert expect == actual[0]


def test_months_with_only_savings(_savings):
    expect = {'date': date(1999, 1, 1), 'X': 0.5, 'total': 0.5}

    actual = MonthsExpenseType(year=1999, expenses=[], **_savings).balance

    assert expect == actual[0]


def test_month_return_dataframe(_ex):
    actual = MonthExpenseType(year=1999, month=1, expenses=_ex[:2]).balance_df

    assert isinstance(actual, pd.DataFrame)
    assert 31 == len(actual)


def test_month_total(_ex):
    actual = MonthExpenseType(year=1999, month=1, expenses=_ex[:2]).total

    assert 0.75 == actual


def test_month_total_no_expenses(_ex):
    actual = MonthExpenseType(year=1999, month=1, expenses=[]).total

    assert 0.0 == actual


def test_month_chart_expenses(_ex):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    actual = obj.chart_expenses(['T1', 'T2', 'T3'])

    expect = [
        {'name': 'T2', 'y': 0.5, 'color': '#6994c7'},
        {'name': 'T1', 'y': 0.25, 'color': '#c86967'},
        {'name': 'T3', 'y': 0., 'color': '#a9c471'},
    ]

    assert expect == actual


def test_month_chart_expenses_no_types(_ex):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    actual = obj.chart_expenses(['T5'])

    expect = [
        {'name': 'T5', 'y': 0.0, 'color': '#6994c7'},
    ]

    assert expect == actual


def test_month_chart_expenses_no_types_no_expenses():
    obj = MonthExpenseType(year=1999, month=1, expenses=[])

    actual = obj.chart_expenses(['T5'])

    expect = [
        {'name': 'T5', 'y': 0.0, 'color': '#6994c7'},
    ]

    assert expect == actual


def test_month_chart_target_categories(_ex, _ex_targets):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    (actual, _, _) = obj.chart_targets(['T1', 'T2', 'T3'], _ex_targets)

    expect = ['T2', 'T1', 'T3']

    assert expect == actual


def test_month_chart_target_data_target(_ex, _ex_targets):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    (_, actual, _) = obj.chart_targets(['T1', 'T2', 'T3'], _ex_targets)

    expect = [0.4, 0.3, 0.0]

    assert expect == actual


def test_month_chart_target_data_target_partial(_ex):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    (_, actual, _) = obj.chart_targets(['T1', 'T2', 'T3'], {'T2': 0.4})

    expect = [0.4, 0.0, 0.0]

    assert expect == actual


def test_month_chart_target_data_target_empty(_ex):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    (_, actual, _) = obj.chart_targets(['T1', 'T2', 'T3'], {})

    expect = [0.0, 0.0, 0.0]

    assert expect == actual


def test_month_chart_target_data_fact(_ex, _ex_targets):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    (_, _, actual) = obj.chart_targets(['T1', 'T2', 'T3'], _ex_targets)

    expect = [
        {'y': 0.5, 'color': 'red'},
        {'y': 0.25, 'color': 'green'},
        {'y': 0.0, 'color': 'green'},
    ]

    assert expect == actual


def test_month_chart_target_data_fact_target_partial(_ex):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    (_, _, actual) = obj.chart_targets(['T1', 'T2', 'T3'], {'T2': 0.4})

    expect = [
        {'y': 0.5, 'color': 'red'},
        {'y': 0.25, 'color': 'green'},
        {'y': 0.0, 'color': 'green'},
    ]

    assert expect == actual


def test_month_chart_target_data_fact_target_empty(_ex):
    obj = MonthExpenseType(year=1999, month=1, expenses=_ex[:2])

    (_, _, actual) = obj.chart_targets(['T1', 'T2', 'T3'], {})

    expect = [
        {'y': 0.5, 'color': 'green'},
        {'y': 0.25, 'color': 'green'},
        {'y': 0.0, 'color': 'green'},
    ]

    assert expect == actual
