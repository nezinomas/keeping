from datetime import date
from types import SimpleNamespace

import polars as pl
import pytest
import time_machine

from ...lib.day_spending import DaySpending


@pytest.fixture(name="df")
def fixture_df():
    exp = [
        {"date": date(1999, 1, 1), "N": 999, "O1": 10, "O2": 125},
        {"date": date(1999, 1, 2), "N": 999, "O1": 0, "O2": 105},
        {"date": date(1999, 1, 3), "N": 999, "O1": 0, "O2": 0},
    ]
    exp = pl.DataFrame(exp)

    exc = [
        {"date": date(1999, 1, 1), "sum": 10},
        {"date": date(1999, 1, 2), "sum": 0},
        {"date": date(1999, 1, 3), "sum": 0},
    ]
    exc = pl.DataFrame(exc)

    return SimpleNamespace(year=1999, month=1, data=exp, exceptions=exc)


@pytest.fixture(name="necessary")
def fixture_necessary():
    return ["N"]


@pytest.fixture(name="df_for_average_calculation")
def fixture_df_for_average_calculation():
    return pl.DataFrame(
        [
            {"total": 11, "date": date(1999, 1, 1)},
            {"total": 21, "date": date(1999, 1, 2)},
            {"total": 31, "date": date(1999, 1, 3)},
            {"total": 41, "date": date(1999, 1, 31)},
        ]
    )


@time_machine.travel("1999-1-2")
def test_avg_per_day(df, necessary):
    obj = DaySpending(
        expense=df,
        necessary=necessary,
        per_day=25,
        free=200,
    )

    actual = obj.avg_per_day

    assert 115 == actual


def test_spending_first_day(df, necessary):
    obj = DaySpending(
        expense=df,
        necessary=necessary,
        per_day=25,
        free=200,
    )

    actual = obj.spending

    assert actual[0]["date"] == date(1999, 1, 1)
    assert actual[0]["day"] == -100
    assert actual[0]["full"] == -100


def test_spending_second_day(df, necessary):
    obj = DaySpending(
        expense=df,
        necessary=necessary,
        per_day=25,
        free=200,
    )

    actual = obj.spending

    assert actual[1]["date"] == date(1999, 1, 2)
    assert actual[1]["day"] == -80
    assert actual[1]["full"] == -180


def test_spending_first_day_necessary_empty(df):
    obj = DaySpending(
        expense=df,
        necessary=[],
        per_day=25,
        free=200,
    )

    actual = obj.spending

    assert actual[0]["date"] == date(1999, 1, 1)
    assert actual[0]["day"] == -1099
    assert actual[0]["full"] == -1099


def test_spending_first_day_necessary_none(df):
    obj = DaySpending(
        expense=df,
        necessary=None,
        per_day=25,
        free=200,
    )

    actual = obj.spending

    assert actual[0]["date"] == date(1999, 1, 1)
    assert actual[0]["day"] == -1099
    assert actual[0]["full"] == -1099


def test_spending_first_day_all_empty(df):
    obj = DaySpending(
        expense=df,
        necessary=None,
        per_day=0,
        free=0,
    )

    actual = obj.spending

    assert actual[0]["date"] == date(1999, 1, 1)
    assert actual[0]["day"] == -1124
    assert actual[0]["full"] == -1124


def test_spending_balance_expenses_empty():
    obj = DaySpending(
        expense=SimpleNamespace(
            year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()
        ),
        necessary=[],
        per_day=0,
        free=0,
    )

    actual = obj.spending

    for x in actual:
        assert x["total"] == 0
        assert x["teoretical"] == 0
        assert x["real"] == 0
        assert x["day"] == 0
        assert x["full"] == 0


@time_machine.travel("1999-1-2")
def test_average_month_two_days(df_for_average_calculation):
    o = DaySpending(
        expense=SimpleNamespace(
            year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()
        ),
        necessary=[],
        per_day=0,
        free=0,
    )

    o._spending = df_for_average_calculation

    actual = o.avg_per_day
    assert 16 == actual


@time_machine.travel("1999-1-31")
def test_average_month_last_day(df_for_average_calculation):
    o = DaySpending(
        expense=SimpleNamespace(
            year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()
        ),
        necessary=[],
        per_day=0,
        free=0,
    )

    o._spending = df_for_average_calculation
    actual = o.avg_per_day

    assert round(actual, 2) == 3.35


@time_machine.travel("1974-1-1")
def test_average_month_other_year(df_for_average_calculation):
    o = DaySpending(
        expense=SimpleNamespace(
            year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()
        ),
        necessary=[],
        per_day=0,
        free=0,
    )

    o._spending = df_for_average_calculation
    actual = o.avg_per_day

    assert round(actual, 2) == 3.35


def test_average_month_empty_dataframe():
    o = DaySpending(
        expense=SimpleNamespace(
            year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()
        ),
        necessary=[],
        per_day=0,
        free=0,
    )

    o._spending = pl.DataFrame()
    actual = o.avg_per_day

    assert actual == 0
