from datetime import date

import pandas as pd
import pytest

from ...expenses.factories import (ExpenseFactory, ExpenseNameFactory,
                                   ExpenseTypeFactory)
from ..services.expenses import ExpenseService

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _expenses():
    t1 = ExpenseTypeFactory(title='T1')
    t2 = ExpenseTypeFactory(title='T2')

    n1  = ExpenseNameFactory(title='N1', parent=t1)
    n2  = ExpenseNameFactory(title='N1', parent=t2)

    ExpenseFactory(date=date(1999, 1, 1), expense_type=t1, expense_name=n1, price=0.25)
    ExpenseFactory(date=date(1999, 12, 1), expense_type=t1, expense_name=n1, price=0.75)

    ExpenseFactory(date=date(1999, 1, 1), expense_type=t2, expense_name=n2, price=0.5)
    ExpenseFactory(date=date(1999, 12, 1), expense_type=t2, expense_name=n2, price=0.35)


def test_balance(_expenses):
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

    obj = ExpenseService(year=1999)
    actual = obj._balance

    assert expect == actual


def test_total_row(_expenses):
    expect = {'T1': 1.0, 'T2': 0.85}

    obj = ExpenseService(year=1999)
    actual = obj._total_row

    assert expect == actual


def test_average(_expenses):
    expect = {'T1': 0.5, 'T2': 0.425}

    obj = ExpenseService(year=1999)
    actual = obj._average

    assert expect == actual


def test_chart_data(_expenses):
    expect = [
        {'name': 'T1', 'y': 1.0},
        {'name': 'T2', 'y': 0.85}
    ]

    obj = ExpenseService(year=1999)
    actual = obj._chart_data()

    assert expect == actual


def test_chart_data_none():
    expect = [{'name': 'Išlaidų nėra', 'y': 0}]

    obj = ExpenseService(year=1999)
    actual = obj._chart_data()

    assert expect == actual


def test_chart_data_empty():
    expect = [{'name': 'Išlaidų nėra', 'y': 0}]

    obj = ExpenseService(year=1999)
    actual = obj._chart_data()

    assert expect == actual


def test_chart_no_data():
    ExpenseTypeFactory(title='X')

    expect = [{'name': 'X', 'y': 0}]

    obj = ExpenseService(year=1999)
    actual = obj._chart_data()

    assert expect == actual


def test_chart_no_data_truncate_long_title():
    ExpenseTypeFactory(title='X'*12)

    obj = ExpenseService(year=1999)
    actual = obj._chart_data()

    assert len(actual[0]['name']) == 11


def test_chart_data_truncate_long_title():
    t1 = ExpenseTypeFactory(title='X'*12)
    ExpenseFactory(date=date(1999, 1, 1), expense_type=t1, price=0.25)

    obj = ExpenseService(year=1999)
    actual = obj._chart_data()

    assert len(actual[0]['name']) == 11


def test_chart_expenses_context():
    obj = ExpenseService(year=1999)

    actual = obj.chart_context()

    assert 'data' in actual


def test_year_expenses_context():
    obj = ExpenseService(year=1999)

    actual = obj.table_context()

    assert 'year' in actual
    assert 'categories' in actual
    assert 'data' in actual
    assert 'total' in actual
    assert 'total_column' in actual
    assert 'total_row' in actual
    assert 'avg' in actual
    assert 'avg_row' in actual
