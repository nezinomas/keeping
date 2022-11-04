from types import SimpleNamespace

import pytest

from ..services.expenses import ExpenseService


@pytest.fixture(name='balance')
def fixture_balance():
    return \
        SimpleNamespace(
            types=['T1', 'T2'],
            total_row={'T1': 1.0, 'T2': 0.85},
            average={'T1': 0.5, 'T2': 0.425},
        )


def test_chart_data(balance):
    expect = [
        {'name': 'T1', 'y': 1.0},
        {'name': 'T2', 'y': 0.85}
    ]

    obj = ExpenseService(data=balance)
    actual = obj.chart_expenses_context()

    assert expect == actual


def test_chart_data_none():
    balance = SimpleNamespace(types=[], total_row={})
    expect = [{'name': 'Išlaidų nėra', 'y': 0}]

    obj = ExpenseService(data=balance)
    actual = obj.chart_expenses_context()

    assert expect == actual


def test_chart_data_empty():
    balance = SimpleNamespace(types=[], total_row={})
    expect = [{'name': 'Išlaidų nėra', 'y': 0}]

    obj = ExpenseService(data=balance)
    actual = obj.chart_expenses_context()

    assert expect == actual


def test_chart_no_data():
    balance = SimpleNamespace(
        types=['X'],
        total_row={},
    )

    expect = [{'name': 'X', 'y': 0}]

    obj = ExpenseService(data=balance)
    actual = obj.chart_expenses_context()

    assert expect == actual


def test_chart_no_data_truncate_long_title():
    balance = SimpleNamespace(
        types=['X'*12],
        total_row={},
    )

    obj = ExpenseService(data=balance)
    actual = obj.chart_expenses_context()

    assert len(actual[0]['name']) == 11


def test_chart_data_truncate_long_title():
    balance = SimpleNamespace(
        types=['X'*12],
        total_row={'X'*12: 0.25}
    )

    obj = ExpenseService(data=balance)
    actual = obj.chart_expenses_context()

    assert len(actual[0]['name']) == 11


def test_yearbalance_context():
    balance = SimpleNamespace(
        types=[],
        total=0.0,
        total_row={},
        total_column={},
        average={},
        balance=[],
    )
    obj = ExpenseService(data=balance)

    actual = obj.table_context()

    assert 'categories' in actual
    assert 'data' in actual
    assert 'total' in actual
    assert 'total_row' in actual
    assert 'avg' in actual
    assert 'avg_row' in actual
