from datetime import date
from types import SimpleNamespace

import pytest

from ...services.detailed import Service


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
        {"date": date(1999, 2, 1), "sum": 1, "title": "X", "type_title": "T"},
        {"date": date(1999, 5, 1), "sum": 2, "title": "X", "type_title": "T"},
    ]


def test_incomes_context_name(data):
    d = SimpleNamespace(
        year=1999, incomes=data, expenses=[], savings=[], expenses_types=[]
    )
    actual = Service(data=d).incomes_context()

    assert actual[0]["name"] == "Pajamos"


def test_incomes_context_data(data):
    d = SimpleNamespace(
        year=1999, incomes=data, expenses=[], savings=[], expenses_types=[]
    )
    actual = Service(data=d).incomes_context()

    assert actual[0]["items"][0]["title"] == "X"
    assert actual[0]["items"][0]["data"] == [1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert actual[0]["items"][1]["title"] == "Y"
    assert actual[0]["items"][1]["data"] == [4, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    assert actual[0]["total_row"] == [5, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert actual[0]["total_col"] == [3, 12]
    assert actual[0]["total"] == 15


def test_incomes_context_data_empty_month():
    data = [
        {"date": date(1999, 1, 1), "sum": 4, "title": "X"},
        {"date": date(1999, 12, 1), "sum": 8, "title": "X"},
    ]
    d = SimpleNamespace(
        year=1999, incomes=data, expenses=[], savings=[], expenses_types=[]
    )
    actual = Service(data=d).incomes_context()

    assert actual[0]["items"][0]["data"] == [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8]


def test_savings_context_name(data):
    d = SimpleNamespace(
        year=1999, incomes=[], expenses=[], savings=data, expenses_types=[]
    )
    actual = Service(data=d).savings_context()

    assert actual[0]["name"] == "Taupymas"


def test_expenses_context_data():
    expenses_data = [
        {"date": date(1999, 2, 1), "sum": 1, "title": "X", "type_title": "A"},
        {"date": date(1999, 6, 1), "sum": 2, "title": "X", "type_title": "A"},
        {"date": date(1999, 2, 1), "sum": 3, "title": "X", "type_title": "T"},
        {"date": date(1999, 6, 1), "sum": 4, "title": "X", "type_title": "T"},
        {"date": date(1999, 1, 1), "sum": 5, "title": "Y", "type_title": "T"},
        {"date": date(1999, 5, 1), "sum": 6, "title": "Y", "type_title": "T"},
    ]

    d = SimpleNamespace(
        year=1999,
        incomes=[],
        expenses=expenses_data,
        savings=[],
        expenses_types=["T", "A"],
    )
    actual = Service(data=d).expenses_context()

    assert actual[0]["name"] == "Išlaidos / A"

    assert actual[0]["items"][0]["title"] == "X"
    assert actual[0]["items"][0]["data"] == [0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0]

    assert actual[0]["total_row"] == [0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0]
    assert actual[0]["total_col"] == [3]
    assert actual[0]["total"] == 3

    assert actual[1]["name"] == "Išlaidos / T"

    assert actual[1]["items"][0]["title"] == "X"
    assert actual[1]["items"][0]["data"] == [0, 3, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0]

    assert actual[1]["items"][1]["title"] == "Y"
    assert actual[1]["items"][1]["data"] == [5, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 0]

    assert actual[1]["total_row"] == [5, 3, 0, 0, 6, 4, 0, 0, 0, 0, 0, 0]
    assert actual[1]["total_col"] == [7, 11]
    assert actual[1]["total"] == 18


def test_expenses_context_data_empty():
    d = SimpleNamespace(
        year=1999,
        incomes=[],
        expenses=[
            {"date": date(1999, 2, 1), "sum": 1, "title": "X", "type_title": "T"}
        ],
        savings=[],
        expenses_types=["A"],
    )
    actual = Service(data=d).expenses_context()

    assert actual == []


def test_insert_type(data):
    actual = Service.insert_type("T", data)

    for r in actual:
        assert r["type_title"] == "T"


def test_modify_data():
    data = [
        {"date": date(1999, 2, 1), "sum": 8, "title": "Y", "type_title": "A"},
        {"date": date(1999, 3, 1), "sum": 8, "title": "X", "type_title": "A"},
    ]

    actual = Service.modify_data(1999, data)

    assert len(actual) == 26

    assert {
        "date": date(1999, 1, 1),
        "sum": 0,
        "title": "Y",
        "type_title": "A",
    } in actual
    assert {
        "date": date(1999, 12, 1),
        "sum": 0,
        "title": "Y",
        "type_title": "A",
    } in actual
    assert {
        "date": date(1999, 1, 1),
        "sum": 0,
        "title": "X",
        "type_title": "A",
    } in actual
    assert {
        "date": date(1999, 12, 1),
        "sum": 0,
        "title": "X",
        "type_title": "A",
    } in actual
