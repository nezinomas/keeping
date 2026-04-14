from datetime import date
from types import SimpleNamespace

import pytest

from ...services.detailed import DetailedTableBuilder


@pytest.fixture(name="data")
def fixture_data():
    return SimpleNamespace(
        data = [
            {"date": date(1999, 1, 1), "sum": 4, "title": "Y"},
            {"date": date(1999, 2, 1), "sum": 8, "title": "Y"},
            {"date": date(1999, 1, 1), "sum": 1, "title": "X"},
            {"date": date(1999, 2, 1), "sum": 2, "title": "X"},
        ]
    )


def test_table_property(data):
    actual = DetailedTableBuilder(data, 1999).table

    assert len(actual[0]) == 14
    assert len(actual[1]) == 14

    assert actual[0]["title"] == "X"
    assert actual[0]["1"] == 1
    assert actual[0]["2"] == 2
    assert actual[0]["3"] == 0
    assert actual[0]["12"] == 0
    assert actual[0]["total_col"] == 3

    assert actual[1]["title"] == "Y"
    assert actual[1]["1"] == 4
    assert actual[1]["2"] == 8
    assert actual[1]["3"] == 0
    assert actual[1]["12"] == 0
    assert actual[1]["total_col"] == 12


def test_table_property_no_data():
    data = SimpleNamespace(data = [])
    actual = DetailedTableBuilder(data, 1999).table

    assert actual == []


def test_total_row_property(data):

    actual = DetailedTableBuilder(data, 1999).total_row

    assert actual["1"] == 5
    assert actual["2"] == 10
    assert actual["3"] == 0
    assert actual["12"] == 0
    assert actual["total_col"] == 15


def test_total_row_property_no_data():
    data = SimpleNamespace(data = [])
    actual = DetailedTableBuilder(data, 1999).total_row

    assert actual =={}
