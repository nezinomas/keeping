from datetime import date
from decimal import Decimal

import pandas as pd
import pytest
from freezegun import freeze_time

from ..lib.day_spending import DaySpending


@pytest.fixture()
def balance_df():
    # N expense type marked as necessary
    # O1, O2 ordinary expense type
    df = pd.DataFrame([
        {'date': pd.datetime(1999, 1, 1), 'N': 9.99,
         'O1': 1.0, 'O2': 1.25, 'total': 12.24},
        {'date': pd.datetime(1999, 1, 2), 'N': 9.99,
         'O1': 0.0, 'O2': 1.05, 'total': 11.04},
        {'date': pd.datetime(1999, 1, 3), 'N': 9.99,
         'O1': 0.0, 'O2': 0.0, 'total': 9.99},
    ])
    df.set_index('date', inplace=True)

    return df


@pytest.fixture()
def necessary():
    return ['N']


@pytest.fixture()
def exceptions():
    return [{'date': date(1999, 1, 1), 'expense_type': 'O2', 'sum': Decimal(1.0)}]


@freeze_time('1999-01-02')
def test_avg_per_day(balance_df, necessary):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=necessary,
                         plan_day_sum=Decimal(0.25), plan_free_sum=Decimal(20)).avg_per_day

    assert 1.65 == actual


def test_spending_first_day(balance_df, necessary):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=necessary,
                         plan_day_sum=Decimal(0.25), plan_free_sum=Decimal(20)).spending

    assert pd.datetime(1999, 1, 1) == actual[0]['date']
    assert -2.0 == actual[0]['day']
    assert -2.0 == actual[0]['full']


def test_spending_second_day(balance_df, necessary):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=necessary,
                         plan_day_sum=Decimal(0.25), plan_free_sum=Decimal(20)).spending

    assert pd.datetime(1999, 1, 2) == actual[1]['date']
    assert -0.8 == actual[1]['day']
    assert -2.8 == pytest.approx(actual[1]['full'], rel=1e-2)


def test_spending_first_day_necessary_empty(balance_df):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=[],
                         plan_day_sum=Decimal(0.25), plan_free_sum=Decimal(20)).spending

    assert pd.datetime(1999, 1, 1) == actual[0]['date']
    assert -11.99 == actual[0]['day']
    assert -11.99 == actual[0]['full']


def test_spending_first_day_necessary_none(balance_df):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=None,
                         plan_day_sum=Decimal(0.25), plan_free_sum=Decimal(20)).spending

    assert pd.datetime(1999, 1, 1) == actual[0]['date']
    assert -11.99 == actual[0]['day']
    assert -11.99 == actual[0]['full']


def test_spending_first_day_all_empty(balance_df):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=[],
                         plan_day_sum=0, plan_free_sum=0).spending

    assert pd.datetime(1999, 1, 1) == actual[0]['date']
    assert -12.24 == actual[0]['day']
    assert -12.24 == actual[0]['full']


def test_spending_first_day_all_none(balance_df):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=None,
                         plan_day_sum=None, plan_free_sum=None).spending

    assert pd.datetime(1999, 1, 1) == actual[0]['date']
    assert -12.24 == actual[0]['day']
    assert -12.24 == actual[0]['full']


def test_spending_with_exceptions_first_day(balance_df, necessary, exceptions):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=necessary,
                         plan_day_sum=Decimal(0.25), plan_free_sum=Decimal(20),
                         exceptions=exceptions).spending

    assert pd.datetime(1999, 1, 1) == actual[0]['date']
    assert -1.0 == actual[0]['day']
    assert -1.0 == actual[0]['full']


def test_spending_with_exceptions_second_day(balance_df, necessary, exceptions):
    actual = DaySpending(year=1999, month=1, month_df=balance_df, necessary=necessary,
                         plan_day_sum=Decimal(0.25), plan_free_sum=Decimal(20),
                         exceptions=exceptions).spending

    assert pd.datetime(1999, 1, 2) == actual[1]['date']
    assert -0.8 == actual[1]['day']
    assert -1.8 == pytest.approx(actual[1]['full'], rel=1e-2)
