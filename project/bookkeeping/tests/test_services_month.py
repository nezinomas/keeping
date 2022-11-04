from decimal import Decimal
from itertools import zip_longest

import pytest
from mock import MagicMock

from ..services.month import MonthService


def test_month_table_context_keys():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    actual = obj.month_table_context()

    assert 'day' in actual
    assert 'expenses' in actual
    assert 'expense_types' in actual
    assert 'total' in actual
    assert 'total_row' in actual
    assert 'total_savings' in actual


@pytest.mark.freeze_time('2017-05-21')
def test_month_table_context_day():
    obj = MonthService(
        data=MagicMock(year=2017, month=5),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    actual = obj.month_table_context()

    assert actual['day'] == 21


@pytest.mark.freeze_time('1999-1-21')
def test_month_table_context_expenses():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(
            total_column=['savings.total_column']
        ),
        spending=MagicMock(
            balance=['spending.balance'],
            total_column=['spending.total_column'],
            spending=['spending.spending']
        )
    )
    actual = obj.month_table_context()['expenses']

    assert isinstance(actual, zip_longest)

    actual = list(actual)[0]

    # spending.balance
    assert actual[0] == 'spending.balance'

    # spending.total_column
    assert actual[1] == 'spending.total_column'

    # spending.spending
    assert actual[2] == 'spending.spending'

    # savings.total_column
    assert actual[3] == 'savings.total_column'


def test_month_table_context_expense_types():
    obj = MonthService(
        data=MagicMock(expense_types=['Expense Type']),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    actual = obj.month_table_context()['expense_types']

    assert actual == ['Expense Type']


def test_month_table_context_total():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock(
            total='spending.total'
        )
    )
    actual = obj.month_table_context()['total']

    assert actual == 'spending.total'


def test_month_table_context_total_row():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock(
            total_row='spending.total_row'
        )
    )
    actual = obj.month_table_context()['total_row']

    assert actual == 'spending.total_row'


def test_month_table_context_total_savings():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(
            total='savings.total'
        ),
        spending=MagicMock()
    )
    actual = obj.month_table_context()['total_savings']

    assert actual == 'savings.total'


@pytest.mark.freeze_time('1999-1-1')
def test_info_context():
    obj = MonthService(
        data=MagicMock(
            incomes=[{'date': 'x', 'sum': Decimal('15')}]
        ),
        plans=MagicMock(
            incomes=10,
            savings=1.2,
            day_input=3,
            remains=-85.3
        ),
        savings=MagicMock(
            total=0.2
        ),
        spending=MagicMock(
            total=0.5,
            avg_per_day=0.02
        )
    )
    actual = obj.info_context()

    assert actual[0]['title'] == 'Pajamos'
    assert actual[0]['plan'] == 10.0
    assert actual[0]['fact'] == 15.0
    assert actual[0]['delta'] == 5.0

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
    assert actual[3]['fact'] == 0.02
    assert actual[3]['delta'] == 2.98

    assert actual[4]['title'] == 'Balansas'
    assert actual[4]['plan'] == -85.3
    assert actual[4]['fact'] == 14.3
    assert actual[4]['delta'] == 99.6


def test_chart_expenses_context():
    obj = MonthService(
        data=MagicMock(
            expense_types=['xyz']
        ),
        plans=MagicMock(),
        savings=MagicMock(
            total=1
        ),
        spending=MagicMock(
            total_row={'xyz': 10}
        )
    )
    actual = obj.chart_expenses_context()

    assert len(actual) == 2
    assert actual[0]['name'] == 'XYZ'
    assert actual[1]['name'] == 'TAUPYMAS'


def test_chart_expenses():
    obj=MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    total_row = {'T1': 0.25, 'T2': 0.5}

    actual = obj._chart_expenses(total_row, ['#1', '#2'])

    expect = [
        {'name': 'T2', 'y': 0.5, 'color': '#1'},
        {'name': 'T1', 'y': 0.25, 'color': '#2'},
    ]

    assert actual == expect


def test_chart_expenses_colors_shorter_then_data():
    obj=MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    total_row = {'T1': 0.25, 'T2': 0.5, 'T3': 0.1}

    actual = obj._chart_expenses(total_row, ['#1', '#2'])

    expect = [
        {'name': 'T2', 'y': 0.5, 'color': '#1'},
        {'name': 'T1', 'y': 0.25, 'color': '#2'},
        {'name': 'T3', 'y': 0.1, 'color': '#1'},
    ]

    assert actual == expect


def test_chart_expenses_no_expenes_data():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )

    actual = obj._chart_expenses(total_row={}, colors=[])

    assert actual == []


def test_chart_targets_context():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    actual = obj.chart_targets_context()

    assert 'categories' in actual
    assert 'target' in actual
    assert 'targetTitle' in actual
    assert 'fact' in actual
    assert 'factTitle' in actual


def test_chart_targets_categories():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )

    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {'T1': 0.3, 'T2': 0.4}

    actual, _, _ = obj._chart_targets(total_row, targets)

    expect = ['T2', 'T1']

    assert actual == expect


def test_chart_targets_data_target():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )

    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {'T1': 0.3, 'T2': 0.4}

    _, actual, _ = obj._chart_targets(total_row, targets)

    expect = [0.4, 0.3]

    assert actual == expect


def test_chart_targets_data_target_empty():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )

    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {}

    _, actual, _ = obj._chart_targets(total_row, targets)

    expect = [0.0, 0.0]

    assert actual == expect


def test_chart_targets_data_fact():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {'T1': 0.3, 'T2': 0.4}

    _, _, actual = obj._chart_targets(total_row, targets)

    expect = [
        {'y': 0.5, 'target': 0.4},
        {'y': 0.25, 'target': 0.3},
    ]

    assert actual == expect


def test_chart_targets_data_fact_no_target():
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )

    total_row = {'T1': 0.25, 'T2': 0.5}
    targets = {}

    _, _, actual = obj._chart_targets(total_row, targets)

    expect = [
        {'y': 0.5, 'target': 0.0},
        {'y': 0.25, 'target': 0.0},
    ]

    assert actual == expect


@pytest.mark.parametrize(
    'data, value, expect',
    [
        ('x', None, 'x'),
        (['x'], None, ['x']),
        ({'x': 1}, None, {'x': 1, 'Taupymas': 0.0}),
        ({'x': 1}, 2, {'x': 1, 'Taupymas': 2}),
    ]
)
def test_append_savings(data, value, expect):
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    obj._append_savings(data, value)

    assert data == expect


@pytest.mark.parametrize(
    'data, expect',
    [
        ({}, []),
        ({'x': 1}, [{'name': 'X', 'y': 1}]),
        ({'a': 1, 'x': 2}, [{'name': 'X', 'y': 2}, {'name': 'A', 'y': 1}]),
    ]
)
def test_make_chart_data(data, expect):
    obj = MonthService(
        data=MagicMock(),
        plans=MagicMock(),
        savings=MagicMock(),
        spending=MagicMock()
    )
    actual = obj._make_chart_data(data)

    assert actual == expect
