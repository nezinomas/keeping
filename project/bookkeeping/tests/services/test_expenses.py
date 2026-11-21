from types import SimpleNamespace

import pytest

from ...services.expenses import ExpenseService


@pytest.fixture(name="balance")
def fixture_balance():
    return SimpleNamespace(
        types=["T1", "T2"],
        total=0,
        total_row={"T1": 1, "T2": 85},
        total_column={},
        balance=[],
        average_over=lambda months: {"T1": 1 / months, "T2": 85 / months},
    )


def test_chart_data(balance):
    expect = [
        {"name": "T2", "y": 85},
        {"name": "T1", "y": 1},
    ]

    obj = ExpenseService(data=balance, months=4)
    actual = obj.chart_context()

    assert expect == actual


def test_chart_data_none(balance):
    balance.types = []
    balance.total_row = {}

    expect = [{"name": "Išlaidų nėra", "y": 0}]

    obj = ExpenseService(data=balance, months=4)
    actual = obj.chart_context()

    assert expect == actual


def test_chart_no_data(balance):
    balance.types = ["X"]
    balance.total_row = {}

    expect = [{"name": "X", "y": 0}]

    obj = ExpenseService(data=balance, months=4)
    actual = obj.chart_context()

    assert expect == actual


@pytest.mark.parametrize(
    "total_row",
    [
        pytest.param({}, id="no_data"),
        pytest.param({"X" * 12: 25}, id="data"),
    ],
)
def test_chart_keeps_a_long_title_whole(balance, total_row):
    # the chart's axis cuts it; a cut name would merge two types into one bar
    balance.types = ["X" * 12]
    balance.total_row = total_row

    obj = ExpenseService(data=balance, months=4)
    actual = obj.chart_context()

    assert actual[0]["name"] == "X" * 12


def test_table_context(balance):
    balance.total = 86
    balance.balance = [{"T1": 1}]
    balance.total_column = [1]

    actual = ExpenseService(data=balance, months=4).table_context()

    assert actual["categories"] == ["T1", "T2"]
    assert list(actual["data"]) == [({"T1": 1}, 1)]
    assert actual["total"] == 86
    assert actual["total_row"] == {"T1": 1, "T2": 85}
    # each type's sum over the four months, and their averages added up
    assert actual["avg"] == 21.5
    assert actual["avg_row"] == {"T1": 0.25, "T2": 21.25}
