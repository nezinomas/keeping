from datetime import date
from types import SimpleNamespace

import polars as pl
import pytest
from freezegun import freeze_time

from ..lib.day_spending import DaySpending


@pytest.fixture(name="df")
def fixture_df():
    exp = [
        {'date': date(1999, 1, 1), 'N': 9.99, 'O1': 1.0, 'O2': 1.25},
        {'date': date(1999, 1, 2), 'N': 9.99, 'O1': 0.0, 'O2': 1.05},
        {'date': date(1999, 1, 3), 'N': 9.99, 'O1': 0.0, 'O2': 0.0},]
    exp = pl.DataFrame(exp)

    exc = [
        {'date': date(1999, 1, 1), 'sum': 1.0},
        {'date': date(1999, 1, 2), 'sum': 0.0},
        {'date': date(1999, 1, 3), 'sum': 0.0},
    ]
    exc = pl.DataFrame(exc)

    return SimpleNamespace(year=1999, month=1, data=exp, exceptions=exc)


@pytest.fixture(name="necessary")
def fixture_necessary():
    return ['N']


@pytest.fixture(name="df_for_average_calculation")
def fixture_df_for_average_calculation():
    return pl.DataFrame([
        {'total': 1.1, 'date': date(1999, 1, 1)},
        {'total': 2.1, 'date': date(1999, 1, 2)},
        {'total': 3.1, 'date': date(1999, 1, 3)},
        {'total': 4.1, 'date': date(1999, 1, 31)},
    ])


@freeze_time('1999-01-02')
def test_avg_per_day(df, necessary):
    obj = DaySpending(
        df=df,
        necessary=necessary,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.avg_per_day

    assert 1.15 == actual


def test_spending_first_day(df, necessary):
    obj = DaySpending(
        df=df,
        necessary=necessary,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.spending

    assert actual[0]['date'] == date(1999, 1, 1)
    assert actual[0]['day'] == -1.0
    assert actual[0]['full'] == -1.0


def test_spending_second_day(df, necessary):
    obj = DaySpending(
        df=df,
        necessary=necessary,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.spending

    assert actual[1]['date'] == date(1999, 1, 2)
    assert actual[1]['day'] == -0.80
    assert round(actual[1]['full'], 2) == -1.80


def test_spending_first_day_necessary_empty(df):
    obj = DaySpending(
        df=df,
        necessary=[],
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.spending

    assert actual[0]['date'] == date(1999, 1, 1)
    assert actual[0]['day'] == -10.99
    assert actual[0]['full'] == -10.99


def test_spending_first_day_necessary_none(df):
    obj = DaySpending(
        df=df,
        necessary=None,
        day_input=0.25,
        expenses_free=20.0,
    )

    actual = obj.spending

    assert actual[0]['date'] == date(1999, 1, 1)
    assert actual[0]['day'] == -10.99
    assert actual[0]['full'] == -10.99


def test_spending_first_day_all_empty(df):
    obj = DaySpending(
        df=df,
        necessary=None,
        day_input=0,
        expenses_free=0,
    )

    actual = obj.spending

    assert actual[0]['date'] == date(1999, 1, 1)
    assert actual[0]['day'] == -11.24
    assert actual[0]['full'] == -11.24


def test_spending_balance_expenses_empty():
    obj = DaySpending(
        df=SimpleNamespace(year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()),
        necessary=[],
        day_input=0,
        expenses_free=0,
    )

    actual = obj.spending

    for x in actual:
        assert x['total'] == 0.0
        assert x['teoretical'] == 0.0
        assert x['real'] == 0.0
        assert x['day'] == 0.0
        assert x['full'] == 0.0


@freeze_time('1999-1-2')
def test_average_month_two_days(df_for_average_calculation):
    o = DaySpending(
        df=SimpleNamespace(year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()),
        necessary=[],
        day_input=0,
        expenses_free=0
    )

    o._spending = df_for_average_calculation

    actual = o.avg_per_day
    assert 1.6 == round(actual, 2)


@freeze_time("1999-01-31")
def test_average_month_last_day(df_for_average_calculation):
    o = DaySpending(
        df=SimpleNamespace(year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()),
        necessary=[],
        day_input=0,
        expenses_free=0
    )

    o._spending = df_for_average_calculation
    actual = o.avg_per_day

    assert round(actual, 2) == 0.34


@freeze_time("1970-01-01")
def test_average_month_other_year(df_for_average_calculation):
    o = DaySpending(
        df=SimpleNamespace(year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()),
        necessary=[],
        day_input=0,
        expenses_free=0
    )

    o._spending = df_for_average_calculation
    actual = o.avg_per_day

    assert round(actual, 2) == 0.34


def test_average_month_empty_dataframe():
    o = DaySpending(
        df=SimpleNamespace(year=1999, month=1, data=pl.DataFrame(), exceptions=pl.DataFrame()),
        necessary=[],
        day_input=0,
        expenses_free=0
    )

    o._spending = pl.DataFrame()
    actual = o.avg_per_day

    assert actual == 0.0
