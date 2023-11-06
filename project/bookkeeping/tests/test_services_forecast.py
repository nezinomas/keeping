import pytest
from ..services import ForecastServiceData
from datetime import date


def test_get_data():
    data = [
        {"date": date(1000, 1, 1), "sum": 1, "title": "incomes"},
        {"date": date(1000, 12, 1), "sum": 2, "title": "incomes"},
    ]

    actual = ForecastServiceData(1000).get_data(data)
    expect = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2]

    assert actual == expect


def test_get_planned_data():
    data = [
        {
            "january": 1,
            "february": None,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": 2,
        }
    ]
    actual = ForecastServiceData(1000).get_planned_data(data)
    expect = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2]

    assert actual == expect


def test_get_planned_data_few_records():
    data = [
        {
            "january": 1,
            "february": None,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": 2,
        },
        {
            "january": 4,
            "february": None,
            "march": None,
            "april": None,
            "may": None,
            "june": None,
            "july": None,
            "august": None,
            "september": None,
            "october": None,
            "november": None,
            "december": 6,
        },
    ]
    actual = ForecastServiceData(1000).get_planned_data(data)
    expect = [5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8]

    assert actual == expect
