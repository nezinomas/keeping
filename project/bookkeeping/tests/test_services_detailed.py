from datetime import date
from types import SimpleNamespace

import pytest

from ..services.detailed import DetailedService


@pytest.fixture(name="data")
def fixture_data():
    return [
        {"date": date(1999, 1, 1), "sum": 4, "title": "Y"},
        {"date": date(1999, 2, 1), "sum": 8, "title": "Y"},
        {"date": date(1999, 1, 1), "sum": 1, "title": "X"},
        {"date": date(1999, 2, 1), "sum": 2, "title": "X"},
    ]


@pytest.fixture(name="expenses_data")
def fixture_expenses_data():
    return [
        {"date": date(1999, 1, 1), "sum": 1, "title": "X", "type_title": "T"},
        {"date": date(1999, 3, 1), "sum": 2, "title": "X", "type_title": "T"},
    ]


def test_incomes_context_name(data):
    d = SimpleNamespace(incomes=data, expenses=[], savings=[], expenses_types=[])
    actual = DetailedService(data=d).incomes_context()

    assert actual[0]["name"] == "Pajamos"


def test_incomes_context_data(data):
    d = SimpleNamespace(incomes=data, expenses=[], savings=[], expenses_types=[])
    actual = DetailedService(data=d).incomes_context()

    assert actual[0]["items"][0]["title"] == "X"
    assert actual[0]["items"][0]["data"] == [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3]
    assert actual[0]["items"][1]["title"] == "Y"
    assert actual[0]["items"][1]["data"] == [4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 12]


def test_incomes_context_data_empty_month():
    data = [
        {"date": date(1999, 1, 1), "sum": 4, "title": "X"},
        {"date": date(1999, 12, 1), "sum": 8, "title": "X"},
    ]
    d = SimpleNamespace(incomes=data, expenses=[], savings=[], expenses_types=[])
    actual = DetailedService(data=d).incomes_context()

    assert actual[0]["items"][0]["data"] == [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 12]


def test_incomes_context_total_row(data):
    d = SimpleNamespace(incomes=data, expenses=[], savings=[], expenses_types=[])
    actual = DetailedService(data=d).incomes_context()

    assert actual[0]["total_row"] == [5, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15]


def test_savings_context_name(data):
    d = SimpleNamespace(incomes=[], expenses=[], savings=data, expenses_types=[])
    actual = DetailedService(data=d).savings_context()

    assert actual[0]["name"] == "Taupymas"


def test_expenses_context_name(expenses_data):
    d = SimpleNamespace(
        incomes=[], expenses=expenses_data, savings=[], expenses_types=["T"]
    )
    actual = DetailedService(data=d).expenses_context()

    assert actual[0]["name"] == "Išlaidos / T"


def test_expenses_context_data(expenses_data):
    d = SimpleNamespace(
        incomes=[], expenses=expenses_data, savings=[], expenses_types=["T"]
    )
    actual = DetailedService(data=d).expenses_context()

    assert actual[0]["items"][0]["title"] == "X"
    assert actual[0]["items"][0]["data"] == [1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3]
