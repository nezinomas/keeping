from datetime import date

import pytest
import time_machine

from ...services.forecast import Data, Forecast, get_month


def test_get_data(main_user):
    main_user.year = 1000

    data = [
        {"date": date(1000, 1, 1), "sum": 1, "title": "incomes"},
        {"date": date(1000, 12, 1), "sum": 2, "title": "incomes"},
    ]

    actual = Data(main_user)._make_data(data)
    expect = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]

    assert actual == expect


def test_get_planned_data(main_user):
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
    main_user.year = 1000
    actual = Data(main_user)._make_planned_data(data)
    expect = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]

    assert actual == expect


def test_get_planned_data_few_records(main_user):
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
    main_user.year = 1000
    actual = Data(main_user)._make_planned_data(data)
    expect = [5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 8.0]

    assert actual == expect


@pytest.fixture(name="data")
def fixture_data():
    return {
        "incomes": [10.0, 11.0, 12.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "expenses": [1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "savings": [4.0, 5.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        "savings_close": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "planned_incomes": [0.0, 0.0, 0.0, 7.0, 8.0, 9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
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
    expect = 12.0

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
    expect = 17.0

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
    actual = Forecast(month=1, data=data_empty).medians()

    assert "expenses" in actual
    assert "savings" in actual


def test_averages_data_with_six_months(data):
    data["expenses"][3] = 6.0
    data["expenses"][4] = 16.0
    data["expenses"][5] = 26.0
    data["savings"][3] = 7.0
    data["savings"][4] = 17.0
    data["savings"][5] = 27.0

    actual = Forecast(month=7, data=data).medians()
    expect = {"expenses": 4.5, "savings": 6.5}

    assert actual == expect


def test_averages_no_data(data_empty):
    actual = Forecast(month=1, data=data_empty).medians()
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


def test_forecast_current_month_incomes_exceeds_planned(data):
    data["incomes"][3] = 100

    actual = Forecast(month=4, data=data).forecast()
    expect = 66

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
