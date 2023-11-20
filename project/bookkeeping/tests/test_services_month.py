from datetime import date

import pytest
import time_machine
from mock import MagicMock

from project.bookkeeping.lib.make_dataframe import MakeDataFrame

from ..services.month import Info, MainTable, Charts, info_table


@time_machine.travel("1999-1-1")
def test_info_context():
    income = 15
    total = {"Viso": 5, "Taupymas": 12}
    per_day = 2
    plans = MagicMock(incomes=100, savings=12, day_input=3, remains=-85)

    actual = info_table(income, total, per_day, plans)

    assert actual["plan"]["income"] == 100
    assert actual["plan"]["saving"] == 12
    assert actual["plan"]["expense"] == 88
    assert actual["plan"]["per_day"] == 3
    assert actual["plan"]["balance"] == -85

    assert actual["fact"]["income"] == 15
    assert actual["fact"]["saving"] == 12
    assert actual["fact"]["expense"] == 5
    assert actual["fact"]["per_day"] == 2
    assert actual["fact"]["balance"] == -2

    assert actual["delta"]["income"] == -85
    assert actual["delta"]["saving"] == 0
    assert actual["delta"]["expense"] == 83
    assert actual["delta"]["per_day"] == 1
    assert actual["delta"]["balance"] == 83


def test_chart_expenses_context():
    totals = {"xyz": 10, "Taupymas": 1}
    targets = {"xyz": 6, "Taupymas": 9}
    obj = Charts(targets, totals)

    actual = obj.chart_expenses()

    assert len(actual) == 2
    assert actual[0]["name"] == "XYZ"
    assert actual[1]["name"] == "TAUPYMAS"


def test_chart_expenses():
    totals = {"T1": 25, "T2": 50}
    obj = Charts(totals=totals, targets={})

    actual = obj.chart_expenses()

    expect = [
        {"name": "T2", "y": 50},
        {"name": "T1", "y": 25},
    ]

    assert actual == expect


def test_chart_expenses_colors_shorter_then_data():
    totals = {"T1": 2, "T2": 5, "T3": 1}
    obj = Charts(targets={}, totals=totals)

    actual = obj.chart_expenses()

    expect = [
        {"name": "T2", "y": 5},
        {"name": "T1", "y": 2},
        {"name": "T3", "y": 1},
    ]

    assert actual == expect


def test_chart_expenses_no_expenes_data():
    obj = Charts(targets={}, totals={})

    actual = obj.chart_expenses()

    assert actual == []


def test_chart_targets_context():
    obj = Charts(targets={}, totals={})
    actual = obj.chart_targets()

    assert "categories" in actual
    assert "target" in actual
    assert "targetTitle" in actual
    assert "fact" in actual
    assert "factTitle" in actual


def test_chart_targets_context_with_savings():
    totals = {"xxx": 6, "Taupymas": 99}
    targets = {"xxx": 6, "Taupymas": 9}
    obj = Charts(targets, totals)
    actual = obj.chart_targets()

    assert actual["categories"] == ["TAUPYMAS", "XXX"]
    assert actual["target"] == [9, 6]
    assert actual["fact"] == [{"y": 99, "target": 9}, {"y": 6, "target": 6}]


def test_chart_targets_categories():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    obj = Charts(targets, totals)


    actual = obj.chart_targets()

    expect = ["T2", "T1"]

    assert actual["categories"] == expect


def test_chart_targets_data_target():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    obj = Charts(targets, totals)

    actual = obj.chart_targets()

    assert actual["target"] == [4, 3]


def test_chart_targets_data_target_empty():
    totals = {"T1": 2, "T2": 5}
    targets = {}
    obj = Charts(targets, totals)

    actual = obj.chart_targets()

    assert actual["target"] == [0, 0]


def test_chart_targets_data_fact():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}
    obj = Charts(targets, totals)

    actual = obj.chart_targets()

    expect = [
        {"y": 5, "target": 4},
        {"y": 2, "target": 3},
    ]

    assert actual["fact"] == expect


def test_chart_targets_data_fact_no_target():
    totals = {"T1": 2, "T2": 5}
    targets = {}
    obj = Charts(targets, totals)

    actual = obj.chart_targets()

    expect = [
        {"y": 5, "target": 0},
        {"y": 2, "target": 0},
    ]

    assert actual["fact"] == expect


@pytest.mark.parametrize(
    "data, expect",
    [
        ({}, []),
        ({"x": 1}, [{"name": "x", "y": 1}]),
        ({"a": 1, "x": 2}, [{"name": "x", "y": 2}, {"name": "a", "y": 1}]),
    ],
)
def test_make_chart_data(data, expect):
    obj = Charts(targets=MagicMock(), totals=MagicMock())
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