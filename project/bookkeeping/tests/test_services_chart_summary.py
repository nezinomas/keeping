from datetime import date
from types import SimpleNamespace

import pytest
import time_machine

from ..services.chart_summary import ChartSummaryService


@pytest.fixture(name="incomes_types")
def fixture_incomes_types():
    return [
        {"date": date(1998, 1, 1), "sum": 1, "title": "T1"},
        {"date": date(2000, 1, 1), "sum": 2, "title": "T1"},
        {"date": date(1999, 1, 1), "sum": 3, "title": "T2"},
        {"date": date(2000, 1, 1), "sum": 4, "title": "T2"},
    ]


def test_chart_incomes_context():
    data = SimpleNamespace(
        incomes=[],
        incomes_types=[],
        salary=[
            {"sum": 12, "year": 1998},
        ],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert "records" in actual
    assert "chart_title" in actual
    assert "categories" in actual
    assert "incomes" in actual
    assert "incomes_title" in actual
    assert "salary" in actual
    assert "salary_title" in actual


@time_machine.travel("1999-1-1")
def test_chart_incomes_salary_years():
    data = SimpleNamespace(
        incomes=[],
        salary=[
            {"sum": 12, "year": 1998},
            {"sum": 10, "year": 1999},
        ],
        incomes_types=[],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert actual["categories"] == [1998, 1999]


@time_machine.travel("1999-1-1")
def test_chart_incomes_salary():
    data = SimpleNamespace(
        incomes=[],
        salary=[
            {"sum": 12, "year": 1998},
            {"sum": 10, "year": 1999},
        ],
        incomes_types=[],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert actual["salary"] == [1, 10]


@time_machine.travel("1999-1-1")
def test_chart_incomes_incomes():
    data = SimpleNamespace(
        incomes=[
            {"sum": 24, "year": 1998},
            {"sum": 12, "year": 1999},
        ],
        incomes_types=[],
        salary=[
            {"sum": 12, "year": 1998},
            {"sum": 10, "year": 1999},
        ],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert actual["incomes"] == [2, 12]


@time_machine.travel("1999-1-1")
def test_chart_incomes_records():
    data = SimpleNamespace(
        incomes=[
            {"sum": 12, "year": 1999},
        ],
        incomes_types=[],
        salary=[
            {"sum": 10, "year": 1999},
        ],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_incomes()

    assert actual["records"] == 1


@time_machine.travel("1999-1-1")
def test_chart_incomes_records_no_data():
    data = SimpleNamespace(incomes=[], incomes_types=[], salary=[], expenses=[])
    actual = ChartSummaryService(data).chart_incomes()

    assert actual["records"] == 0

    assert "chart_title" not in actual
    assert "categories" not in actual
    assert "incomes" not in actual
    assert "incomes_title" not in actual
    assert "salary" not in actual
    assert "salary_title" not in actual


def test_chart_balance_context():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {"sum": 12, "year": 1998},
        ],
        incomes_types=[],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert "records" in actual
    assert "chart_title" in actual
    assert "categories" in actual
    assert "incomes" in actual
    assert "incomes_title" in actual
    assert "expenses" in actual
    assert "expenses_title" in actual


def test_chart_balance_no_data():
    data = SimpleNamespace(salary=[], incomes=[], incomes_types=[], expenses=[])
    actual = ChartSummaryService(data).chart_balance()

    assert actual["records"] == 0
    assert "chart_title" not in actual
    assert "categories" not in actual
    assert "incomes" not in actual
    assert "incomes_title" not in actual
    assert "expenses" not in actual
    assert "expenses_title" not in actual


def test_chart_balance_records_only_incomes():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {"sum": 12, "year": 1998},
        ],
        incomes_types=[],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual["records"] == 1


def test_chart_balance_records_only_expenses():
    data = SimpleNamespace(
        salary=[],
        incomes=[],
        incomes_types=[],
        expenses=[
            {"sum": 12, "year": 1998},
        ],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual["records"] == 1


def test_chart_balance_records():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {"sum": 12, "year": 1998},
        ],
        incomes_types=[],
        expenses=[
            {"sum": 12, "year": 1998},
            {"sum": 24, "year": 1999},
        ],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual["records"] == 1


def test_chart_balance_categories_only_incomes():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {"sum": 12, "year": 1998},
            {"sum": 24, "year": 1999},
        ],
        incomes_types=[],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual["categories"] == [1998, 1999]


def test_chart_balance_categories_only_expenses():
    data = SimpleNamespace(
        salary=[],
        incomes=[],
        incomes_types=[],
        expenses=[
            {"sum": 12, "year": 1998},
            {"sum": 24, "year": 1999},
        ],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual["categories"] == [1998, 1999]


def test_chart_balance_categories():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {"sum": 12, "year": 1998},
            {"sum": 24, "year": 1999},
        ],
        incomes_types=[],
        expenses=[
            {"sum": 12, "year": 2000},
        ],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual["categories"] == [1998, 1999]


def test_chart_balance_incomes():
    data = SimpleNamespace(
        salary=[],
        incomes=[
            {"sum": 12, "year": 1998},
            {"sum": 24, "year": 1999},
        ],
        incomes_types=[],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual["incomes"] == [12, 24]


def test_chart_balance_expenses():
    data = SimpleNamespace(
        salary=[],
        incomes=[],
        incomes_types=[],
        expenses=[
            {"sum": 12, "year": 1998},
            {"sum": 24, "year": 1999},
        ],
    )
    actual = ChartSummaryService(data).chart_balance()

    assert actual["expenses"] == [12, 24]


def test_chart_incomes_types_context():
    data = SimpleNamespace(
        incomes=[],
        incomes_types=[],
        salary=[],
        expenses=[],
    )
    actual = ChartSummaryService(data).chart_incomes_types()

    assert "chart_title" in actual
    assert "categories" in actual
    assert "data" in actual


def test_chart_incomes_types_categories_no_data():
    data = SimpleNamespace(
        incomes=[],
        salary=[],
        expenses=[],
        incomes_types=[]
    )
    actual = ChartSummaryService(data).chart_incomes_types()

    assert actual["categories"] == []


def test_chart_incomes_types_categories(incomes_types):
    data = SimpleNamespace(
        incomes=[],
        salary=[],
        expenses=[],
        incomes_types=incomes_types
    )
    actual = ChartSummaryService(data).chart_incomes_types()

    assert actual["categories"] == [1998, 1999, 2000]


def test_chart_incomes_types_data(incomes_types):
    data = SimpleNamespace(
        incomes=[],
        salary=[],
        expenses=[],
        incomes_types=incomes_types
    )
    actual = ChartSummaryService(data).chart_incomes_types()

    assert actual["data"][0] == {"name": "T1", "data": [1, 0, 2]}
    assert actual["data"][1] == {"name": "T2", "data": [0, 3, 4]}


def test_chart_incomes_types_data_no_data():
    data = SimpleNamespace(
        incomes=[],
        salary=[],
        expenses=[],
        incomes_types=[]
    )
    actual = ChartSummaryService(data).chart_incomes_types()

    assert actual["data"] == []