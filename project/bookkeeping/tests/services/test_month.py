from datetime import date

import pytest
import time_machine
from mock import MagicMock, PropertyMock

from project.bookkeeping.lib.make_dataframe import MakeDataFrame

from ...services.month import (
    ChartBuilder,
    InfoBuilder,
    InfoState,
    MonthTableBuilder,
)


def test_chart_expenses_context():
    totals = {"xyz": 10, "Taupymas": 1}
    targets = {"xyz": 6, "Taupymas": 9}
    obj = ChartBuilder(targets, totals)

    actual = obj.build_expenses()

    assert len(actual) == 2
    assert actual[0]["name"] == "XYZ"
    assert actual[1]["name"] == "TAUPYMAS"


def test_chart_expenses():
    totals = {"T1": 25, "T2": 50}
    obj = ChartBuilder(totals=totals, targets={})

    actual = obj.build_expenses()

    expect = [
        {"name": "T2", "y": 50},
        {"name": "T1", "y": 25},
    ]

    assert actual == expect


def test_chart_expenses_colors_shorter_then_data():
    totals = {"T1": 2, "T2": 5, "T3": 1}
    obj = ChartBuilder(targets={}, totals=totals)

    actual = obj.build_expenses()

    expect = [
        {"name": "T2", "y": 5},
        {"name": "T1", "y": 2},
        {"name": "T3", "y": 1},
    ]

    assert actual == expect


def test_chart_expenses_no_expenes_data():
    obj = ChartBuilder(targets={}, totals={})

    actual = obj.build_expenses()

    assert actual == []


def test_build_targets_context():
    obj = ChartBuilder(targets={}, totals={})
    actual = obj.build_targets()

    assert "categories" in actual
    assert "target" in actual
    assert "targetTitle" in actual
    assert "fact" in actual
    assert "factTitle" in actual


def test_build_targets_context_with_savings():
    totals = {"xxx": 6, "Taupymas": 99}
    targets = {"xxx": 6, "Taupymas": 9}
    obj = ChartBuilder(targets, totals)
    actual = obj.build_targets()

    assert actual["categories"] == ["TAUPYMAS", "XXX"]
    assert actual["target"] == [9, 6]
    assert actual["fact"] == [{"y": 99, "target": 9}, {"y": 6, "target": 6}]


def test_build_targets_categories():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    expect = ["T2", "T1"]

    assert actual["categories"] == expect


def test_build_targets_data_target():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}

    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    assert actual["target"] == [4, 3]


def test_build_targets_data_target_empty():
    totals = {"T1": 2, "T2": 5}
    targets = {}
    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    assert actual["target"] == [0, 0]


def test_build_targets_data_fact():
    totals = {"T1": 2, "T2": 5}
    targets = {"T1": 3, "T2": 4}
    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    expect = [
        {"y": 5, "target": 4},
        {"y": 2, "target": 3},
    ]

    assert actual["fact"] == expect


def test_build_targets_data_fact_no_target():
    totals = {"T1": 2, "T2": 5}
    targets = {}
    obj = ChartBuilder(targets, totals)

    actual = obj.build_targets()

    expect = [
        {"y": 5, "target": 0},
        {"y": 2, "target": 0},
    ]

    assert actual["fact"] == expect


@pytest.fixture(name="df_expense")
def fixture_df_expense():
    year = 1999
    month = 3
    data = [{"date": date(1999, 3, 2), "title": "A", "sum": 4, "exception_sum": 0}]
    columns = ["A", "B"]

    return MakeDataFrame(year=year, month=month, data=data, columns=columns).data


@pytest.fixture(name="df_saving")
def fixture_df_saving():
    year = 1999
    month = 3
    data = [{"date": date(1999, 3, 3), "sum": 2, "title": "Taupymas"}]

    return MakeDataFrame(year=year, month=month, data=data).data


def test_main_table(df_expense, df_saving):
    actual = MonthTableBuilder(df_expense, df_saving).table

    assert len(actual) == 31
    assert actual[0] == {
        "date": date(1999, 3, 1),
        "A": 0,
        "B": 0,
        "Viso": 0,
        "Taupymas": 0,
    }
    assert actual[1] == {
        "date": date(1999, 3, 2),
        "A": 4,
        "B": 0,
        "Viso": 4,
        "Taupymas": 0,
    }
    assert actual[2] == {
        "date": date(1999, 3, 3),
        "A": 0,
        "B": 0,
        "Viso": 0,
        "Taupymas": 2,
    }


def test_main_table_total_row(df_expense, df_saving):
    actual = MonthTableBuilder(df_expense, df_saving).total_row

    assert actual == {"A": 4, "B": 0, "Viso": 4, "Taupymas": 2}


def test_info_builder_delta():
    fact = InfoState(income=9, saving=8, expense=7, per_day=6, balance=5)
    plan = InfoState(income=1, saving=2, expense=3, per_day=4, balance=4)

    actual = InfoBuilder.build(fact, plan)

    assert actual["fact"] == {
        "income": 9,
        "saving": 8,
        "expense": 7,
        "per_day": 6,
        "balance": 5,
    }
    assert actual["plan"] == {
        "income": 1,
        "saving": 2,
        "expense": 3,
        "per_day": 4,
        "balance": 4,
    }
    assert actual["delta"] == {
        "income": 8,
        "saving": -6,
        "expense": -4,
        "per_day": -2,
        "balance": 1,
    }
