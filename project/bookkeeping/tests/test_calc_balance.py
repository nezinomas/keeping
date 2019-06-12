import pytest
from ..lib.stats_utils import CalcBalance
import pandas as pd


@pytest.fixture
def _balance():
    df = pd.DataFrame({
        'title': ['AAA', 'BBB'],
        'action_col': [0.0, 0.0],
    })
    df.set_index('title', inplace=True)
    return df


@pytest.fixture
def _df():
    df = pd.DataFrame({
        'name': ['AAA', 'AAA', 'x'],
        'summed_col': [1.2, 5.3, 9],
    })
    return df


def test_sum(_balance, _df):
    cb = CalcBalance(groupby_col='name', balance=_balance)
    cb.calc(_df, '+', 'action_col', 'summed_col')

    assert _balance.at['AAA', 'action_col'] == 6.5
    assert _balance.at['BBB', 'action_col'] == 0.0


def test_sum_empty(_balance):
    cb = CalcBalance(groupby_col='name', balance=_balance)
    cb.calc(pd.DataFrame(), '+', 'action_col', 'summed_col')

    assert _balance.at['AAA', 'action_col'] == 0.0
    assert _balance.at['BBB', 'action_col'] == 0.0


def test_sum_none(_balance):
    cb = CalcBalance(groupby_col='name', balance=_balance)
    cb.calc(None, '+', 'action_col', 'summed_col')

    assert _balance.at['AAA', 'action_col'] == 0.0
    assert _balance.at['BBB', 'action_col'] == 0.0


def test_sum_no_index_in_balance(_balance, _df):
    _b = _balance.reset_index()

    cb = CalcBalance(groupby_col='name', balance=_b)
    cb.calc(None, '+', 'action_col', 'summed_col')

    assert _balance.at['AAA', 'action_col'] == 0.0
    assert _balance.at['BBB', 'action_col'] == 0.0


def test_sub(_balance, _df):
    cb = CalcBalance(groupby_col='name', balance=_balance)
    cb.calc(_df, '-', 'action_col', 'summed_col')

    assert _balance.at['AAA', 'action_col'] == -6.5
    assert _balance.at['BBB', 'action_col'] == 0.0
