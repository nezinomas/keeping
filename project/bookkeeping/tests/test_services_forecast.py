import pytest
from datetime import date
from ..services.forecast import ForecastService, ForecastServiceData


def test_get_data():
    data = [
        {"date": date(1000, 1, 1), "sum": 1, "title": "incomes"},
        {"date": date(1000, 12, 1), "sum": 2, "title": "incomes"},
    ]

    actual = ForecastServiceData(1000)._make_data(data)
    expect = [1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 2.]

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
    actual = ForecastServiceData(1000)._make_planned_data(data)
    expect = [1., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 2.]

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
    actual = ForecastServiceData(1000)._make_planned_data(data)
    expect = [5., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 8.]

    assert actual == expect


@pytest.fixture(name="data")
def fixture_data():
    return {
        "incomes": [10., 11., 12., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
        "expenses": [1., 2., 3., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
        "savings": [4., 5., 6., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
        "planned_incomes": [0., 0., 0., 7., 8., 9., 0., 0., 0., 0., 0., 0.],
    }


def test_balance(data):
    actual = ForecastService(month=4, data=data).balance()
    expect = 12.

    assert actual == expect


def test_planned_incomes(data):
    actual = ForecastService(month=4, data=data).planned_incomes()
    expect = 24.

    assert actual == expect


def test_averages_for_fourt_months(data):
    actual = ForecastService(month=4, data=data).averages()
    expect = {"expenses": 2., "savings": 5.}

    assert actual == expect


def test_averages_data_with_six_months(data):
    data["expenses"][3] = 6.
    data["expenses"][4] = 16.
    data["expenses"][5] = 26.
    data["savings"][3] = 7.
    data["savings"][4] = 17.
    data["savings"][5] = 27.

    actual = ForecastService(month=7, data=data).averages()
    expect = {"expenses": 16., "savings": 17.}

    assert actual == expect


def test_averages_for_three_months(data):
    actual = ForecastService(month=3, data=data).averages()
    expect = {"expenses": 1.5, "savings": 4.5}

    assert actual == expect

def test_forecast(data):
    actual = ForecastService(month=4, data=data).forecast()
    expect = -27.

    assert actual == expect
