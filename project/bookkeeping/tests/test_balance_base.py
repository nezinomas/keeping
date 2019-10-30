import pandas as pd
import pytest
from freezegun import freeze_time

from ...core.mixins.balance_base import (BalanceBase, df_days_of_month,
                                         df_months_of_year)


def create_df():
    df = pd.DataFrame({'t': [1.1], 'date': ['x']})
    df.set_index('date', inplace=True)

    return df


data_balance = [
    (create_df(), [{'t': 1.1, 'date': 'x'}]),
    (pd.DataFrame(), []),
    (None, [])
]


@pytest.mark.parametrize("df,expected", data_balance)
def test_balance(df, expected):
    o = BalanceBase()
    o._balance = df

    assert o.balance == expected


@pytest.mark.parametrize("df,expected", data_balance)
def test_balance_then_before_was_called_total_row(df, expected):
    o = BalanceBase()
    o._balance = df

    o.total_row

    assert o.balance == expected


data_average = [
    (pd.DataFrame({'t': [1.1, 2.2]}), {'t': 1.65}),
    (pd.DataFrame({'t': [0.0, 1.1, 0, 2.2]}), {'t': 1.65}),
    (pd.DataFrame({'t': [0.0, pd.NaT]}), {}),
    (pd.DataFrame(), {}),
    (None, {})
]


@pytest.mark.parametrize('df,expected', data_average)
def test_average(df, expected):
    o = BalanceBase()
    o._balance = df

    assert pytest.approx(o.average, rel=1e-2) == expected


data_total_row = [
    (pd.DataFrame({'x': [1.05, 2.05]}), {'x': 3.1}),
    (pd.DataFrame(), {}),
    (None, {}),
]


@pytest.mark.parametrize('df,expected', data_total_row)
def test_total_row(df, expected):
    o = BalanceBase()
    o._balance = df

    assert pytest.approx(o.total_row, rel=1e-2) == expected


def test_df_days_of_month():
    actual = df_days_of_month(2020, 2)

    assert 29 == len(actual)

    assert 'date' == actual.index.name


data_days_of_month = [
    (2020, 22),
    (2020, 'x'),
    ('y', 'x')
]


@pytest.mark.parametrize('year,month', data_days_of_month)
def test_df_days_of_month_invalid(year, month):
    actual = df_days_of_month(2020, 22)

    assert actual.empty


def test_df_months_of_year():
    actual = df_months_of_year(2020)

    assert 12 == len(actual)

    assert 'date' == actual.index.name

    assert pd.Timestamp(2020, 1, 1) == actual.index[0]
    assert pd.Timestamp(2020, 12, 1) == actual.index[-1]


@pytest.mark.parametrize('year', [('x'), (1)])
def test_df_months_of_year_invalid(year):
    actual = df_months_of_year(year)

    assert actual.empty


@pytest.fixture()
def df():
    df = pd.DataFrame([
        {'t': 1.1, 'date': pd.datetime(1999, 1, 1)},
        {'t': 2.1, 'date': pd.datetime(1999, 1, 2)},
        {'t': 3.1, 'date': pd.datetime(1999, 1, 3)},
        {'t': 4.1, 'date': pd.datetime(1999, 1, 31)},
    ])
    df.set_index('date', inplace=True)

    return df


@freeze_time("1999-01-02")
def test_average_month_two_days(df):
    o = BalanceBase()
    o._balance = df

    actual = o.average_month(1999, 1)
    assert 1.6 == round(actual['t'], 2)


@freeze_time("1999-01-31")
def test_average_month_last_day(df):
    o = BalanceBase()
    o._balance = df

    actual = o.average_month(1999, 1)

    assert 0.34 == round(actual['t'], 2)


@freeze_time("1970-01-01")
def test_average_month_other_year(df):
    o = BalanceBase()
    o._balance = df

    actual = o.average_month(1999, 1)

    assert 0.34 == round(actual['t'], 2)


def test_average_month_empty_dataframe():
    o = BalanceBase()
    o._balance = pd.DataFrame()

    actual = o.average_month(1999, 1)
    assert {} == actual


def test_average_month_no_dataframe():
    o = BalanceBase()
    o._balance = None

    actual = o.average_month(1999, 1)
    assert {} == actual
