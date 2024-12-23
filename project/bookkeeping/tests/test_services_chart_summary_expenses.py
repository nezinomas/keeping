from types import SimpleNamespace

import pytest

from ..services.chart_summary_expenses import ChartSummaryExpensesService


@pytest.fixture(name="types")
def fixure_types():
    return [
        {"year": 2000, "sum": 5, "title": "X"},
        {"year": 2002, "sum": 15, "title": "X"},
        {"year": 2001, "sum": 12, "title": "Y"},
        {"year": 2000, "sum": 2, "title": "Y"},
    ]


@pytest.fixture(name="names")
def fixture_names():
    return [
        {"year": 2000, "sum": 5, "title": "X / A"},
        {"year": 2000, "sum": 2, "title": "Y / B"},
        {"year": 2001, "sum": 12, "title": "Y / B"},
        {"year": 2002, "sum": 15, "title": "X / A"},
    ]


def test_categories(types):
    data = SimpleNamespace(data=types)
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.categories

    assert actual == [2000, 2001, 2002]


def test_categories_sorting(names):
    names.append({"year": 1999, "sum": 15, "title": "A", "root": "X"})
    data = SimpleNamespace(data=names)
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.categories

    assert actual == [1999, 2000, 2001, 2002]


def test_categories_no_data():
    data = SimpleNamespace(data=[])
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.categories

    assert actual == []


def test_serries_data_types(types):
    data = SimpleNamespace(data=types)
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.serries_data
    expect = [
        {"name": "X", "data": [5, 0, 15]},
        {"name": "Y", "data": [2, 12, 0]},
    ]

    assert actual == expect


def test_serries_data_types_empty():
    data = SimpleNamespace(data=[])
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.serries_data

    assert actual == []


def test_serries_data_names(names):
    data = SimpleNamespace(data=names)
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.serries_data
    expect = [
        {"name": "X / A", "data": [5, 0, 15]},
        {"name": "Y / B", "data": [2, 12, 0]},
    ]

    assert actual == expect


def test_serries_data_full(types, names):
    data = SimpleNamespace(data=types + names)
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.serries_data
    expect = [
        {"name": "X", "data": [5, 0, 15]},
        {"name": "X / A", "data": [5, 0, 15]},
        {"name": "Y", "data": [2, 12, 0]},
        {"name": "Y / B", "data": [2, 12, 0]},
    ]
    assert actual == expect


def test_serries_total_column(types):
    data = SimpleNamespace(data=types)
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.total_col
    expect = {"X": 20, "Y": 14}

    assert actual == expect


def test_serries_total_row(types):
    data = SimpleNamespace(data=types)
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.total_row
    expect = [7, 12, 15]

    assert actual == expect


def test_serries_total(types):
    data = SimpleNamespace(data=types)
    obj = ChartSummaryExpensesService(data=data)

    actual = obj.total

    assert actual == 34
