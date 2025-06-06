from datetime import date

import pytest

from ..services.detailed_one_category import Service


@pytest.fixture(name="data")
def fixure_data():
    return [
        {"date": date(2021, 1, 1), "sum": 12, "title": "X", "type_title": "T2"},
        {"date": date(2021, 11, 1), "sum": 1, "title": "X", "type_title": "T2"},
        {"date": date(2021, 1, 1), "sum": 2, "title": "Y", "type_title": "T2"},
        {"date": date(2021, 11, 1), "sum": 24, "title": "Y", "type_title": "T2"},
    ]


def test_order_by_title_no_data():
    actual = Service(2021, [], order="title").context

    assert actual == {}


def test_order_by_title(data):
    actual = Service(2021, data, order="title").context

    assert actual["name"] == "Išlaidos / T2"

    assert actual["items"][0]["title"] == "X"
    assert actual["items"][0]["data"] == [12.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0]
    assert actual["items"][1]["title"] == "Y"
    assert actual["items"][1]["data"] == [2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.0, 0]

    assert actual["total_row"] == [14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25.0, 0]
    assert actual["total_col"] == [13.0, 26.0]
    assert actual["total"] == 39.0


def test_order_by_title_for_savings():
    data = [
        {"date": date(2021, 1, 1), "sum": 12, "title": "X"},
        {"date": date(2021, 11, 1), "sum": 1, "title": "X"},
        {"date": date(2021, 1, 1), "sum": 2, "title": "Y"},
        {"date": date(2021, 11, 1), "sum": 24, "title": "Y"},
    ]
    actual = Service(2021, data, order="title", category="savings").context

    assert actual["name"] == "Taupymas"

    assert actual["items"][0]["title"] == "X"
    assert actual["items"][0]["data"] == [12.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0]
    assert actual["items"][1]["title"] == "Y"
    assert actual["items"][1]["data"] == [2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.0, 0]

    assert actual["total_row"] == [14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25.0, 0]
    assert actual["total_col"] == [13.0, 26.0]
    assert actual["total"] == 39.0


def test_order_by_month_november(data):
    actual = Service(2021, data, order="nov").context

    assert actual["name"] == "Išlaidos / T2"

    assert actual["items"][0]["title"] == "Y"
    assert actual["items"][0]["data"] == [2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.0, 0]
    assert actual["items"][1]["title"] == "X"
    assert actual["items"][1]["data"] == [12.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0]

    assert actual["total_row"] == [14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25.0, 0]
    assert actual["total_col"] == [26.0, 13.0]
    assert actual["total"] == 39.0


def test_order_by_total_col(data):
    actual = Service(2021, data, order="total").context

    assert actual["name"] == "Išlaidos / T2"

    assert actual["items"][0]["title"] == "Y"
    assert actual["items"][0]["data"] == [2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 24.0, 0]
    assert actual["items"][1]["title"] == "X"
    assert actual["items"][1]["data"] == [12.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0, 0]

    assert actual["total_row"] == [14.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 25.0, 0]
    assert actual["total_col"] == [26.0, 13.0]
    assert actual["total"] == 39.0
