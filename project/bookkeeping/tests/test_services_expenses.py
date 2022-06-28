from datetime import date

import pandas as pd
import pytest

from ...expenses.factories import ExpenseFactory, ExpenseTypeFactory
from ..services.expenses import ExpensesService

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _expenses():
    t1 = ExpenseTypeFactory(title='T1')
    t2 = ExpenseTypeFactory(title='T2')

    ExpenseFactory(date=date(1999, 1, 1), expense_type=t1, price=0.25)
    ExpenseFactory(date=date(1999, 12, 1), expense_type=t1, price=0.75)

    ExpenseFactory(date=date(1999, 1, 1), expense_type=t2, price=0.5)
    ExpenseFactory(date=date(1999, 12, 1), expense_type=t2, price=0.35)


def test_balance(_expenses, rf):
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

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._balance

    assert expect == actual


def test_total_row(_expenses, rf):
    expect = {'T1': 1.0, 'T2': 0.85}

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._total_row

    assert expect == actual


def test_average(_expenses, rf):
    expect = {'T1': 0.5, 'T2': 0.425}

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._average

    assert expect == actual


def test_chart_data(_expenses, rf):
    expect = [
        {'name': 'T1', 'y': 1.0},
        {'name': 'T2', 'y': 0.85}
    ]

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._chart_data()

    assert expect == actual


def test_chart_data_none(rf):
    expect = [{'name': 'Išlaidų nėra', 'y': 0}]

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._chart_data()

    assert expect == actual


def test_chart_data_empty(rf):
    expect = [{'name': 'Išlaidų nėra', 'y': 0}]

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._chart_data()

    assert expect == actual


def test_chart_no_data(rf):
    ExpenseTypeFactory(title='X')

    expect = [{'name': 'X', 'y': 0}]

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._chart_data()

    assert expect == actual


def test_chart_no_data_truncate_long_title(rf):
    ExpenseTypeFactory(title='X'*12)

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._chart_data()

    assert len(actual[0]['name']) == 11


def test_chart_data_truncate_long_title(rf):
    t1 = ExpenseTypeFactory(title='X'*12)
    ExpenseFactory(date=date(1999, 1, 1), expense_type=t1, price=0.25)

    obj = ExpensesService(request=rf, year=1999)
    actual = obj._chart_data()

    assert len(actual[0]['name']) == 11
