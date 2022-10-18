from datetime import date, datetime
from itertools import zip_longest

import pytest

from ...expenses.factories import ExpenseFactory
from ...plans.factories import (DayPlanFactory, ExpensePlanFactory,
                                IncomePlanFactory, NecessaryPlanFactory,
                                SavingPlanFactory)
from ...savings.factories import SavingFactory
from ..services.month import MonthService

pytestmark = pytest.mark.django_db


@pytest.fixture()
def _expenses():
    ExpenseFactory(date=date(1999, 1, 1), price=0.2)
    ExpenseFactory(date=date(1999, 1, 1), price=0.3)


@pytest.fixture()
def _savings():
    SavingFactory(date=date(1999, 1, 1), price=0.1)
    SavingFactory(date=date(1999, 1, 1), price=0.1)


@pytest.fixture()
def _plans():
    IncomePlanFactory(january=10)
    ExpensePlanFactory(january=5)
    NecessaryPlanFactory(january=1.1)
    SavingPlanFactory(january=1.2)
    DayPlanFactory(january=3)


@pytest.fixture()
def _month_data(_expenses, _savings, _plans):
    pass


def test_month_table_context_keys():
    obj = MonthService(year=1999, month=1)
    actual = obj.month_table_context()

    assert 'day' in actual
    assert 'expenses' in actual
    assert 'expense_types' in actual
    assert 'total' in actual
    assert 'total_row' in actual
    assert 'total_savings' in actual


@pytest.mark.freeze_time('2017-05-21')
def test_month_table_context_day():
    obj = MonthService(year=2017, month=5)
    actual = obj.month_table_context()

    assert actual['day'] == 21


@pytest.mark.freeze_time('1999-1-21')
def test_month_table_context_expenses(_month_data):
    obj = MonthService(year=1999, month=1)
    actual = obj.month_table_context()['expenses']

    assert isinstance(actual, zip_longest)

    actual = list(actual)[0]

    # spending.balance
    assert actual[0] == {
        'date': datetime(1999, 1, 1),
        'Expense Type': 0.5,
    }

    # spending.total_column
    assert actual[1] == {
        'date': datetime(1999, 1, 1),
        'total': 0.5,
    }

    # spending.spending
    assert actual[2] == {
        'date': datetime(1999, 1, 1),
        'total': 0.5,
        'teoretical': 4.7,
        'real': 7.2,
        'day': 2.5,
        'full': 2.5,
    }

    # savings.total_column
    assert actual[3] == {
        'date': datetime(1999, 1, 1),
        'total': 0.2,
    }


@pytest.mark.freeze_time('1999-1-21')
def test_month_table_context_expense_types(_month_data):
    obj = MonthService(year=1999, month=1)
    actual = obj.month_table_context()['expense_types']

    assert actual == ['Expense Type']


@pytest.mark.freeze_time('1999-1-21')
def test_month_table_context_total(_month_data):
    obj = MonthService(year=1999, month=1)
    actual = obj.month_table_context()['total']

    assert actual == 0.5


@pytest.mark.freeze_time('1999-1-21')
def test_month_table_context_total_row(_month_data):
    obj = MonthService(year=1999, month=1)
    actual = obj.month_table_context()['total_row']

    assert actual == {'Expense Type': 0.5}


@pytest.mark.freeze_time('1999-1-21')
def test_month_table_context_total_savings(_month_data):
    obj = MonthService(year=1999, month=1)
    actual = obj.month_table_context()['total_savings']

    assert actual == 0.2


@pytest.mark.freeze_time('1999-1-21')
def test_info_context(_month_data):
    obj = MonthService(year=1999, month=1)
    actual = obj.info_context()

    assert actual[0]['title'] == 'Pajamos'
    assert actual[0]['plan'] == 10.0
    assert actual[0]['fact'] == 0.0
    assert actual[0]['delta'] == -10.0

    assert actual[1]['title'] == 'Išlaidos'
    assert actual[1]['plan'] == 8.8
    assert actual[1]['fact'] == 0.5
    assert actual[1]['delta'] == 8.3

    assert actual[2]['title'] == 'Taupymas'
    assert actual[2]['plan'] == 1.2
    assert actual[2]['fact'] == 0.2
    assert actual[2]['delta'] == 1.0

    assert actual[3]['title'] == 'Pinigai dienai'
    assert actual[3]['plan'] == 3.0
    assert round(actual[3]['fact'], 2) == 0.02
    assert round(actual[3]['delta'], 2) == 2.98

    assert actual[4]['title'] == 'Balansas'
    assert actual[4]['plan'] == -85.3
    assert actual[4]['fact'] == -0.7
    assert actual[4]['delta'] == 84.6


@pytest.mark.freeze_time('1999-1-21')
def test_chart_expenses_context(_month_data):
    obj = MonthService(year=1999, month=1)
    actual = obj.chart_expenses_context()

    assert len(actual) == 2
    assert actual[0]['name'] == 'EXPENSE TYPE'
    assert actual[1]['name'] == 'TAUPYMAS'


@pytest.mark.freeze_time('1999-1-21')
def test_chart_targets_context(_month_data):
    obj = MonthService(year=1999, month=1)
    actual = obj.chart_targets_context()

    assert 'categories' in actual
    assert 'target' in actual
    assert 'targetTitle' in actual
    assert 'fact' in actual
    assert 'factTitle' in actual


def test_chart_expenses():
    types = ['T1', 'T2', 'T3']
    total_row = {'T1': 0.25, 'T2': 0.5}

    obj = MonthService(year=1999, month=1)

    actual = obj._chart_expenses(types, total_row)

    expect = [
        {'name': 'T2', 'y': 0.5, 'color': '#6994c7'},
        {'name': 'T1', 'y': 0.25, 'color': '#c86967'},
        {'name': 'T3', 'y': 0., 'color': '#a9c471'},
    ]

    assert expect == actual


def test_chart_expenses_no_expenes_data():
    types = ['T1']
    total_row = {}

    obj = MonthService(year=1999, month=1)

    actual = obj._chart_expenses(types, total_row)

    expect = [
        {'name': 'T1', 'y': 0.0, 'color': '#6994c7'},
    ]

    assert expect == actual


def test_chart_expenses_no_types_and_no_expenes_data():
    types = []
    total_row = {}

    obj = MonthService(year=1999, month=1)

    actual = obj._chart_expenses(types, total_row)

    expect = []

    assert expect == actual

def test_chart_expenses_no_types_and_no_expenes_data():
    types = []
    total_row = {}

    obj = MonthService(year=1999, month=1)

    actual = obj._chart_expenses(types, total_row)

    expect = []

    assert expect == actual


def test_chart_targets_categories():
    types = ['T1', 'T2', 'T3']
    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {'T1': 0.3, 'T2': 0.4}

    obj = MonthService(year=1999, month=1)

    actual, _, _ = obj._chart_targets(types, total_row, targets)

    expect = ['T2', 'T1', 'T3']

    assert expect == actual


def test_chart_targets_data_target():
    types = ['T1', 'T2', 'T3']
    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {'T1': 0.3, 'T2': 0.4}

    obj = MonthService(year=1999, month=1)

    _, actual, _ = obj._chart_targets(types, total_row, targets)

    expect = [0.4, 0.3, 0.0]

    assert expect == actual


def test_chart_targets_data_target_empty():
    types = ['T1', 'T2', 'T3']
    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {}

    obj = MonthService(year=1999, month=1)

    _, actual, _ = obj._chart_targets(types, total_row, targets)

    expect = [0.0, 0.0, 0.0]

    assert expect == actual


def test_chart_targets_data_fact():
    types = ['T1', 'T2', 'T3']
    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {'T1': 0.3, 'T2': 0.4}

    obj = MonthService(year=1999, month=1)

    _, _, actual = obj._chart_targets(types, total_row, targets)

    expect = [
        {'y': 0.5, 'target': 0.4},
        {'y': 0.25, 'target': 0.3},
        {'y': 0.0, 'target': 0.0},
    ]

    assert expect == actual


def test_chart_targets_data_fact_no_data():
    types = ['T1', 'T2', 'T3']
    total_row = {}
    targets = {'T1': 0.3, 'T2': 0.4}

    obj = MonthService(year=1999, month=1)

    _, _, actual = obj._chart_targets(types, total_row, targets)

    expect = [
        {'y': 0.0, 'target': 0.3},
        {'y': 0.0, 'target': 0.4},
        {'y': 0.0, 'target': 0.0},
    ]

    assert expect == actual


def test_chart_targets_data_fact_no_target():
    types = ['T1', 'T2', 'T3']
    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {}

    obj = MonthService(year=1999, month=1)

    _, _, actual = obj._chart_targets(types, total_row, targets)

    expect = [
        {'y': 0.5, 'target': 0.0},
        {'y': 0.25, 'target': 0.0},
        {'y': 0.0, 'target': 0.0},
    ]

    assert expect == actual


def test_chart_targets_data_fact_no_data_and_no_target():
    types = ['T1', 'T2', 'T3']
    total_row = {}
    targets = {}

    obj = MonthService(year=1999, month=1)

    _, _, actual = obj._chart_targets(types, total_row, targets)

    expect = [
        {'y': 0.0, 'target': 0.0},
        {'y': 0.0, 'target': 0.0},
        {'y': 0.0, 'target': 0.0},
    ]

    assert expect == actual
