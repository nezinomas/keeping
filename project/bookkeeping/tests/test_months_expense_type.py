import pytest

from datetime import date
from decimal import Decimal

import pytest

from ..lib.months_expense_type import MonthsExpenseType as T


@pytest.fixture
def _ex():
    return ([
        {'date': date(1999, 1, 1), 'sum': Decimal(0.5), 'title': 'T1'},
        {'date': date(1999, 1, 1), 'sum': Decimal(0.25), 'title': 'T2'},
        {'date': date(1999, 12, 1), 'sum': Decimal(0.75), 'title': 'T1'},
        {'date': date(1999, 12, 1), 'sum': Decimal(0.35), 'title': 'T2'},
    ])


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

    actual = T(_ex).balance

    assert expect == actual


def test_months_expense_type_totals(_ex):
    expect = {'T1': 1.25, 'T2': 0.6, 'total': 1.85}

    actual = T(_ex).totals

    assert expect == actual


def test_months_expense_type_average(_ex):
    expect = {'T1': 0.625, 'T2': 0.3, 'total': 0.925}

    actual = T(_ex).average

    assert expect == actual


def test_months_expense_chart_data(_ex):
    expect = [
        {'name': 'T1', 'y': 1.25},
        {'name': 'T2', 'y': 0.6}
    ]

    actual = T(_ex).chart_data

    assert expect == actual


def test_months_expense_chart_data_none():
    expect = []

    actual = T(None).chart_data

    assert expect == actual


def test_months_expense_chart_data_empty():
    expect = []

    actual = T([]).chart_data

    assert expect == actual
