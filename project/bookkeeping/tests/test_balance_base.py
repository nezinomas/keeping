import numpy as np
import pandas as pd
import pytest

from ..lib.balance_base import BalanceBase


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
    o._data = df

    assert o.balance == expected


@pytest.mark.parametrize("df,expected", data_balance)
def test_balance_then_before_was_called_total_row(df, expected):
    o = BalanceBase()
    o._data = df

    o.total_row

    assert o.balance == expected


data_average = [
    (pd.DataFrame({'t': [1.1, 2.2]}), {'t': 1.65}),
    (pd.DataFrame({'t': [0.0, 1.1, 0, 2.2]}), {'t': 1.65}),
    (pd.DataFrame({'t': pd.Series([0.0, np.nan], dtype='float64')}), {'t': 0.0}),
    (pd.DataFrame(), {}),
    (None, {}),
    (pd.DataFrame({'t1': [1.1, 2.2], 't2': [0, 0]}), {'t1': 1.65, 't2': 0.0}),
]


@pytest.mark.parametrize('df,expected', data_average)
def test_average(df, expected):
    o = BalanceBase()
    o._data = df

    assert pytest.approx(o.average, rel=1e-2) == expected


data_total_row = [
    (pd.DataFrame({'x': [1.05, 2.05]}), {'x': 3.1}),
    (pd.DataFrame(), {}),
    (None, {}),
]


@pytest.mark.parametrize('df,expected', data_total_row)
def test_total_row(df, expected):
    o = BalanceBase()
    o._data = df

    assert pytest.approx(o.total_row, rel=1e-2) == expected
