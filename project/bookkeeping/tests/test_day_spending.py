import pandas as pd
import pytest

from ..lib.day_spending import DaySpending


@pytest.fixture()
def balance_df():
    # N expense type marked as necessary
    # O1, O2 ordinary expense type
    df = pd.DataFrame([
        {'date': pd.datetime(1999, 1, 1), 'N': 9.99, 'O1': 1.0, 'O2': 1.25},
        {'date': pd.datetime(1999, 1, 2), 'N': 9.99, 'O1': 0.0, 'O2': 1.05},
        {'date': pd.datetime(1999, 1, 3), 'N': 9.99, 'O1': 0.0, 'O2': 0.0},
    ])
    df.set_index('date', inplace=True)

    return df


@pytest.fixture()
def necessary():
    return ['N']


@pytest.fixture
def day_sum():
    return {'january': 0.25, 'february': 1.0}


@pytest.fixture
def free_expenses():
    return {'january': 20.0, 'february': 1.0}


def test_avg_per_day(balance_df, necessary, day_sum, free_expenses):
    actual = DaySpending(1, balance_df, necessary,
                         day_sum, free_expenses).avg_per_day

    assert 1.65 == actual


def test_plan_per_day(balance_df, necessary, day_sum, free_expenses):
    actual = DaySpending(1, balance_df, necessary,
                         day_sum, free_expenses).plan_per_day

    assert 0.25 == actual


def test_plan_free_sum(balance_df, necessary, day_sum, free_expenses):
    actual = DaySpending(1, balance_df, necessary,
                         day_sum, free_expenses).plan_free_sum

    assert 20.0 == actual


def test_spending_first_day(balance_df, necessary, day_sum, free_expenses):
    actual = DaySpending(1, balance_df, necessary,
                         day_sum, free_expenses).spending

    assert pd.datetime(1999, 1, 1) == actual[0]['date']
    assert -2.0 == actual[0]['day']
    assert -2.0 == actual[0]['full']


def test_spending_second_day(balance_df, necessary, day_sum, free_expenses):
    actual = DaySpending(1, balance_df, necessary,
                         day_sum, free_expenses).spending

    assert pd.datetime(1999, 1, 2) == actual[1]['date']
    assert -0.8 == actual[1]['day']
    assert -2.8 == pytest.approx(actual[1]['full'], rel=1e-2)
