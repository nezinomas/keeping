import pandas as pd
import pytest

from ..mixins.calc_balance import CalcBalanceMixin as T


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
    actual = T().balance(df)

    assert actual == expected


data_average = [
    (pd.DataFrame({'t': [1.1, 2.2]}), {'t': 1.65}),
    (pd.DataFrame({'t': [0.0, 1.1, 0, 2.2]}), {'t': 1.65}),
    (pd.DataFrame({'t': [0.0, pd.NaT]}), {}),
    (pd.DataFrame(), {}),
    (None, {})
]


@pytest.mark.parametrize('df,expected', data_average)
def test_average(df, expected):
    actual = T().average(df)

    assert pytest.approx(actual, rel=1e-2) == expected


data_totals = [
    (pd.DataFrame({'x': [1.05, 2.05]}), {'x': 3.1}),
    (pd.DataFrame(), {}),
    (None, {}),
]


@pytest.mark.parametrize('df,expected', data_totals)
def test_totals(df, expected):
    actual = T().totals(df)

    assert pytest.approx(actual, rel=1e-2) == expected


def test_df_days_of_month():
    actual = T().df_days_of_month(2020, 2)

    assert 29 == len(actual)

    assert 'date' == actual.index.name
    assert 'total' in actual


data_days_of_month = [
    (2020, 22, None),
    (2020, 'x', None),
    ('y', 'x', None)
]


@pytest.mark.parametrize('year,month,expected', data_days_of_month)
def test_df_days_of_month_invalid(year, month, expected):
    actual = T().df_days_of_month(2020, 22)

    assert expected == actual


def test_df_months_of_year():
    actual = T().df_months_of_year(2020)

    assert 12 == len(actual)

    assert 'date' == actual.index.name
    assert 'total' in actual

    assert pd.Timestamp(2020, 1, 1) == actual.index[0]
    assert pd.Timestamp(2020, 12, 1) == actual.index[-1]


@pytest.mark.parametrize('year,expected', [('x', None), (1, None)])
def test_df_months_of_year_invalid(year, expected):
    actual = T().df_months_of_year(year)

    assert expected == actual
