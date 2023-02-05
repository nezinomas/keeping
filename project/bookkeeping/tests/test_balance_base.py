from datetime import date

import polars as pl
import pytest

from ..lib.balance_base import BalanceBase


@pytest.fixture(name="df")
def fixture_df():
    arr = [
        {'date': date(1999, 1, 1), 'x': 1.1, 'y': 2.1},
        {'date': date(1999, 1, 2), 'x': 1.1, 'y': 2.1},
        {'date': date(1999, 1, 3), 'x': 0.0, 'y': 2.1},
        {'date': date(1999, 1, 4), 'x': 1.1, 'y': 0.0},
    ]
    return pl.DataFrame(arr)


@pytest.mark.parametrize(
    'df, expected',
    [
        (None, []),
        (pl.DataFrame(), []),
        (pl.DataFrame({'t': [1.1], 'date': ['x']}), [{'t': 1.1, 'date': 'x'}]),
    ]
)
def test_balance(df, expected):
    actual = BalanceBase(df).balance

    assert actual == expected


@pytest.mark.parametrize(
    'data, expected',
    [
        (None, []),
        (pl.DataFrame(), []),
        (pl.DataFrame({'t': [1.1], 'date': ['x']}), [{'t': 1.1, 'date': 'x'}]),
    ]
)
def test_balance_then_before_was_called_total_row(data, expected):
    obj = BalanceBase(data)

    obj.total_row

    assert obj.balance == expected


@pytest.mark.parametrize(
    'data, expected',
    [
        (None, {}),
        (pytest.lazy_fixture('df'), {'x': 1.1, 'y': 2.1}),
        (pl.DataFrame({'x': [1.1, 2.2]}), {'x': 1.65}),
        (pl.DataFrame({'x': [0.0, 1.1, 0, 2.2]}), {'x': 1.65}),
        (pl.DataFrame({'x': pl.Series([0.0, None], dtype=pl.Float32)}), {'x': 0.0}),
        (pl.DataFrame({'t1': [1.1, 2.2], 't2': [0, 0]}), {'t1': 1.65, 't2': 0.0}),
    ]
)
def test_average(data, expected):
    actual = BalanceBase(data).average

    assert pytest.approx(actual, rel=1e-2) == expected


@pytest.mark.parametrize(
    'data, expected',
    [
        (pytest.lazy_fixture('df'), {'x': 3.3, 'y': 6.3}),
        (pl.DataFrame(), {}),
        (None, {}),
    ]
)
def test_total_row(data, expected):
    actual = BalanceBase(data).total_row

    assert pytest.approx(actual, rel=1e-2) == expected


def test_total_column(df):
    actual = BalanceBase(df).total_column

    expect = [
        {'date': date(1999, 1, 1), 'total': 3.2},
        {'date': date(1999, 1, 2), 'total': 3.2},
        {'date': date(1999, 1, 3), 'total': 2.1},
        {'date': date(1999, 1, 4), 'total': 1.1},
    ]

    assert actual == expect


def test_total(df):
    actual = BalanceBase(df).total

    assert actual == 9.6


def test_types(df):
    actual = BalanceBase(df).types

    assert actual == ['x', 'y']
