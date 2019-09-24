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
