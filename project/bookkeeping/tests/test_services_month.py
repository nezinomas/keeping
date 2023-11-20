from datetime import date
from types import SimpleNamespace

import pytest
import time_machine
from mock import MagicMock

from project.bookkeeping.lib.make_dataframe import MakeDataFrame

from ..services.month import Info, MainTable, Charts


@time_machine.travel("1999-1-1")
def test_info_context():
    obj = Charts(
        data=MagicMock(incomes=[{"date": "x", "sum": 15}]),
        plans=MagicMock(incomes=100, savings=12, day_input=3, remains=-85),
        savings=MagicMock(total=2),
        spending=MagicMock(total=5, avg_per_day=2),
    )
    actual = obj.info_context()

    assert actual[0]["title"] == "Pajamos"
    assert actual[0]["plan"] == 100
    assert actual[0]["fact"] == 15

    assert actual[1]["title"] == "Išlaidos"
    assert actual[1]["plan"] == 88
    assert actual[1]["fact"] == 5

    assert actual[2]["title"] == "Taupymas"
    assert actual[2]["plan"] == 12
    assert actual[2]["fact"] == 2

    assert actual[3]["title"] == "Pinigai dienai"
    assert actual[3]["plan"] == 3
    assert actual[3]["fact"] == 2

    assert actual[4]["title"] == "Balansas"
    assert actual[4]["plan"] == -85
    assert actual[4]["fact"] == 8


def test_chart_expenses_context():
    obj = Charts(
        data=MagicMock(expense_types=["xyz"]),
        plans=MagicMock(),
        savings=MagicMock(total=1),
        spending=MagicMock(total_row={"xyz": 10}),
    )
    actual = obj.chart_expenses_context()

    assert len(actual) == 2
    assert actual[0]["name"] == "XYZ"
    assert actual[1]["name"] == "TAUPYMAS"


def test_chart_expenses():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )
    total_row = {"T1": 25, "T2": 50}

    actual = obj._chart_data_for_expenses(total_row)

    expect = [
        {"name": "T2", "y": 50},
        {"name": "T1", "y": 25},
    ]

    assert actual == expect


def test_chart_expenses_colors_shorter_then_data():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )
    total_row = {"T1": 2, "T2": 5, "T3": 1}

    actual = obj._chart_data_for_expenses(total_row)

    expect = [
        {"name": "T2", "y": 5},
        {"name": "T1", "y": 2},
        {"name": "T3", "y": 1},
    ]

    assert actual == expect


def test_chart_expenses_no_expenes_data():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )

    actual = obj._chart_data_for_expenses(total_row={})

    assert actual == []


def test_chart_targets_context():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )
    actual = obj.chart_targets_context()

    assert "categories" in actual
    assert "target" in actual
    assert "targetTitle" in actual
    assert "fact" in actual
    assert "factTitle" in actual


def test_chart_targets_context_with_savings():
    obj = Charts(
        data=MagicMock(),
        plans=SimpleNamespace(targets={'XXX': 6}, savings=9),
        savings=SimpleNamespace(total=99),
        spending=SimpleNamespace(total_row={'XXX': 66})
    )
    actual = obj.chart_targets_context()

    assert actual["categories"] == ["TAUPYMAS", "XXX"]
    assert actual["target"] == [9, 6]
    assert actual["fact"] == [{"y": 99, "target": 9}, {"y": 66, "target": 6}]


def test_chart_targets_categories():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )

    total_row = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    actual, _, _ = obj._chart_data_for_targets(total_row, targets)

    expect = ["T2", "T1"]

    assert actual == expect


def test_chart_targets_data_target():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )

    total_row = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    _, actual, _ = obj._chart_data_for_targets(total_row, targets)

    expect = [4, 3]

    assert actual == expect


def test_chart_targets_data_target_empty():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )

    total_row = {"T1": 2, "T2": 5}
    targets = {}

    _, actual, _ = obj._chart_data_for_targets(total_row, targets)

    expect = [0, 0]

    assert actual == expect


def test_chart_targets_data_fact():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )
    total_row = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    _, _, actual = obj._chart_data_for_targets(total_row, targets)

    expect = [
        {"y": 5, "target": 4},
        {"y": 2, "target": 3},
    ]

    assert actual == expect


def test_chart_targets_data_fact_no_target():
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )

    total_row = {"T1": 2, "T2": 5}
    targets = {}

    _, _, actual = obj._chart_data_for_targets(total_row, targets)

    expect = [
        {"y": 5, "target": 0},
        {"y": 2, "target": 0},
    ]

    assert actual == expect


@pytest.mark.parametrize(
    "data, expect",
    [
        ({}, []),
        ({"x": 1}, [{"name": "x", "y": 1}]),
        ({"a": 1, "x": 2}, [{"name": "x", "y": 2}, {"name": "a", "y": 1}]),
    ],
)
def test_make_chart_data(data, expect):
    obj = Charts(
        data=MagicMock(), plans=MagicMock(), savings=MagicMock(), spending=MagicMock()
    )
    actual = obj._make_chart_data(data)

    assert actual == expect


@pytest.fixture(name="df_expense")
def fixture_df_expense():
    year = 1999
    month = 3
    data = [{"date": date(1999, 3, 2), "title": "A", "sum": 4, "exception_sum": 0}]
    columns = ["A", "B"]

    return MakeDataFrame(year=year, month=month, data=data, columns=columns)


@pytest.fixture(name="df_saving")
def fixture_df_saving():
    year = 1999
    month = 3
    data = [{'date': date(1999, 3, 3), 'sum': 2, 'title': 'Taupymas'}]

    return MakeDataFrame(year=year, month=month, data=data)


def test_main_table(df_expense, df_saving):
    actual = MainTable(df_expense, df_saving).table

    assert len(actual) == 31
    assert actual[0] == {"date": date(1999, 3, 1), "A": 0, "B": 0, "Viso": 0, "Taupymas": 0}
    assert actual[1] == {"date": date(1999, 3, 2), "A": 4, "B": 0, "Viso": 4, "Taupymas": 0}
    assert actual[2] == {"date": date(1999, 3, 3), "A": 0, "B": 0, "Viso": 0, "Taupymas": 2}


def test_main_table_total_row(df_expense, df_saving):
    actual = MainTable(df_expense, df_saving).total_row

    assert actual == {"A": 4, "B": 0, "Viso": 4, "Taupymas": 2}


def test_info_class_sub_method():
    a = Info(income=9, saving=8, expense=7, per_day=6, balance=5)
    b = Info(income=1, saving=2, expense=3, per_day=4, balance=4)

    actual = a - b

    assert isinstance(actual, Info)

    assert actual.income == -8
    assert actual.saving == 6
    assert actual.expense == 4
    assert actual.per_day == 2
    assert actual.balance == -1