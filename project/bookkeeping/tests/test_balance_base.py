from datetime import date

import polars as pl
import pytest

from ..lib.balance_base import BalanceBase


def create_df():
    return pl.DataFrame({'t': [1.1], 'date': ['x']})


@pytest.mark.parametrize(
    'df, expected',
    [
        (create_df(), [{'t': 1.1, 'date': 'x'}]),
        (pl.DataFrame(), []),
        (None, [])
    ]
)
def test_balance(df, expected):
    o = BalanceBase(df)

    assert o.balance == expected


@pytest.mark.parametrize(
    'df, expected',
    [
        (create_df(), [{'t': 1.1, 'date': 'x'}]),
        (pl.DataFrame(), []),
        (None, [])
    ]
)
def test_balance_then_before_was_called_total_row(df, expected):
    o = BalanceBase(df)

    o.total_row

    assert o.balance == expected


@pytest.mark.parametrize(
    'df, expected',
    [
        (None, {}),
        (pl.DataFrame(), {}),
        (pl.DataFrame({'t': [1.1, 2.2]}), {'t': 1.65}),
        (pl.DataFrame({'t': [0.0, 1.1, 0, 2.2]}), {'t': 1.65}),
        (pl.DataFrame({'t': pl.Series([0.0, None], dtype=pl.Float32)}), {'t': 0.0}),
        (pl.DataFrame({'t1': [1.1, 2.2], 't2': [0, 0]}), {'t1': 1.65, 't2': 0.0}),
    ]
)
def test_average(df, expected):
    actual = BalanceBase(df).average

    assert pytest.approx(actual, rel=1e-2) == expected


@pytest.mark.parametrize(
    'df, expected',
    [
        (pl.DataFrame([
            {'date': date(1999, 1, 1), 'x': 1.1, 'y': 2.0},
            {'date': date(1999, 1, 2), 'x': 1.1, 'y': 2.3},]),
         {'x': 2.2, 'y': 4.3}),
        (pl.DataFrame(), {}),
        (None, {}),
    ]
)
def test_total_row(df, expected):
    actual = BalanceBase(df).total_row

    assert pytest.approx(actual, rel=1e-2) == expected


def test_total_column():
    arr = [
        {'date': date(1999, 1, 1), 'x': 1.1, 'y': 2.0},
        {'date': date(1999, 1, 2), 'x': 1.1, 'y': 2.3},
    ]
    df = pl.DataFrame(arr)
    actual = BalanceBase(df).total_column

    expect = [
        {'date': date(1999, 1, 1), 'total': 3.1},
        {'date': date(1999, 1, 2), 'total': 3.4},
    ]

    assert actual == expect


def test_total():
    arr = [
        {'date': date(1999, 1, 1), 'x': 1.1, 'y': 2.0},
        {'date': date(1999, 1, 2), 'x': 1.1, 'y': 2.3},
    ]
    df = pl.DataFrame(arr)
    actual = BalanceBase(df).total

    assert actual == 6.5


def test_types():
    arr = [
        {'date': date(1999, 1, 1), 'x': 1.1, 'y': 2.0},
        {'date': date(1999, 1, 2), 'x': 1.1, 'y': 2.3},
    ]
    df = pl.DataFrame(arr)
    actual = BalanceBase(df).types

    assert actual == ['x', 'y']
