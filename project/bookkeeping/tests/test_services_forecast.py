from datetime import date

import pytest
import time_machine

from ..services.forecast import Forecast, Data, get_month


def test_get_data():
    data = [
        {"date": date(1000, 1, 1), "sum": 1, "title": "incomes"},
        {"date": date(1000, 12, 1), "sum": 2, "title": "incomes"},
    ]

    actual = Data(1000)._make_data(data)
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
    actual = Data(1000)._make_planned_data(data)
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
    actual = Data(1000)._make_planned_data(data)
    expect = [5., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 8.]

    assert actual == expect


@pytest.fixture(name="data")
def fixture_data():
    return {
        "incomes": [10., 11., 12., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
        "expenses": [1., 2., 3., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
        "savings": [4., 5., 6., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
        "savings_close": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "planned_incomes": [0., 0., 0., 7., 8., 9., 0., 0., 0., 0., 0., 0.],
    }


@pytest.fixture(name="data_empty")
def fixture_data_empty():
    return {
        "incomes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "expenses": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "savings": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "savings_close": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "planned_incomes": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }


def test_current_month(data):
    actual = Forecast(month=4, data=data).current_month()

    assert "expenses" in actual
    assert "savings" in actual
    assert "incomes" in actual
    assert "planned_incomes" in actual


def test_balance(data):
    actual = Forecast(month=4, data=data).balance()
    expect = 12.

    assert actual == expect


def test_balance_with_savings_close(data):
    data["savings_close"][2] = 2
    actual = Forecast(month=4, data=data).balance()
    expect = 14

    assert actual == expect


def test_balance_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).balance()
    expect = 0

    assert actual == expect


def test_planned_incomes(data):
    actual = Forecast(month=4, data=data).planned_incomes()
    expect = 24.

    assert actual == expect


def test_planned_incomes_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).planned_incomes()
    expect = 0

    assert actual == expect


def test_planned_incomes_only_planned_data(data_empty):
    data_empty["planned_incomes"][3] = 1
    actual = Forecast(month=1, data=data_empty).planned_incomes()
    expect = 1

    assert actual == expect


def test_averages_dict_keys(data_empty):
    actual = Forecast(month=1, data=data_empty).averages()

    assert "expenses" in actual
    assert "savings" in actual


def test_averages_data_with_six_months(data):
    data["expenses"][3] = 6.
    data["expenses"][4] = 16.
    data["expenses"][5] = 26.
    data["savings"][3] = 7.
    data["savings"][4] = 17.
    data["savings"][5] = 27.

    actual = Forecast(month=7, data=data).averages()
    expect = {"expenses": 9., "savings": 11.}

    assert actual == expect


def test_averages_for_three_months(data):
    actual = Forecast(month=3, data=data).averages()
    expect = {"expenses": 1.5, "savings": 4.5}

    assert actual == expect


def test_averages_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).averages()
    expect = {"expenses": 0, "savings": 0}

    assert actual == expect


def test_forecast(data):
    actual = Forecast(month=4, data=data).forecast()
    expect = -27

    assert actual == expect


def test_forecast_with_savings_close(data):
    data["savings_close"][2] = 2
    actual = Forecast(month=4, data=data).forecast()
    expect = -25

    assert actual == expect


def test_forecast_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).forecast()
    expect = 0

    assert actual == expect


def test_forecast_only_planned_data(data_empty):
    data_empty["planned_incomes"][3] = 1
    actual = Forecast(month=1, data=data_empty).forecast()
    expect = 1

    assert actual == expect


def test_forecast_current_month_expenses_exceeds_average(data):
    data["expenses"][3] = 100

    actual = Forecast(month=4, data=data).forecast()
    expect = -125

    assert actual == expect


def test_forecast_current_month_savings_exceeds_average(data):
    data["savings"][3] = 100

    actual = Forecast(month=4, data=data).forecast()
    expect = -122

    assert actual == expect


@time_machine.travel("1999-3-1")
@pytest.mark.parametrize(
    "year, expected",
    [
        (1999, 3),
        (1998, 12),
        (2000, 1),
    ],
)
def test_get_month(year, expected):
    assert get_month(year) == expected