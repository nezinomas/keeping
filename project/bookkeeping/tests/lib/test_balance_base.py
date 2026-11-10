from datetime import date

import polars as pl
import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from ...lib.balance_base import BalanceBase

ARR = pl.DataFrame(
    [
        {"date": date(1999, 1, 1), "x": 11, "y": 21},
        {"date": date(1999, 1, 2), "x": 11, "y": 21},
        {"date": date(1999, 1, 3), "x": 0, "y": 21},
        {"date": date(1999, 1, 4), "x": 11, "y": 0},
    ]
)


@pytest.fixture(name="df")
def fixture_df():
    return ARR


@pytest.mark.parametrize(
    "df, expected",
    [
        (None, []),
        (pl.DataFrame(), []),
        (pl.DataFrame({"t": [11], "date": ["x"]}), [{"t": 11, "date": "x"}]),
    ],
)
def test_balance(df, expected):
    actual = BalanceBase(df).balance

    assert actual == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        (None, []),
        (pl.DataFrame(), []),
        (pl.DataFrame({"t": [11], "date": ["x"]}), [{"t": 11, "date": "x"}]),
    ],
)
def test_balance_then_before_was_called_total_row(data, expected):
    obj = BalanceBase(data)

    _ = obj.total_row

    assert obj.balance == expected


def _frame(columns):
    if not columns:
        return pl.DataFrame()
    days = len(next(iter(columns.values())))
    return pl.DataFrame(
        {"date": [date(1999, 1, 1)] * days}
        | {name: pl.Series(values, dtype=pl.Int64) for name, values in columns.items()}
    )


def _mean_of_the_months_with_a_value(column):
    values = [value for value in column if value]
    return sum(values) / len(values) if values else 0


COLUMNS = st.one_of(
    st.none(),
    st.integers(1, 12).flatmap(
        lambda days: st.dictionaries(
            st.sampled_from(["x", "y", "t1", "t2"]),
            st.lists(
                st.one_of(st.none(), st.integers(0, 1000)),
                min_size=days,
                max_size=days,
            ),
            max_size=4,
        )
    ),
)


@given(columns=COLUMNS)
@example(columns=None)
@example(columns={})
@example(columns={"x": [11, 11, 0, 11], "y": [21, 21, 21, 0]})
@example(columns={"x": [11, 22]})
@example(columns={"x": [0, 11, 0, 22]})
@example(columns={"x": [0, None]})
@example(columns={"t1": [11, 22], "t2": [0, 0]})
def test_average_is_the_mean_of_each_column_over_its_months_with_a_value(columns):
    data = None if columns is None else _frame(columns)

    actual = BalanceBase(data).average

    assert actual == pytest.approx(
        {
            name: _mean_of_the_months_with_a_value(column)
            for name, column in (columns or {}).items()
        }
    )


@pytest.mark.parametrize(
    "data, expected",
    [
        (ARR, {"x": 33, "y": 63}),
        (pl.DataFrame(), {}),
        (None, {}),
    ],
)
def test_total_row(data, expected):
    actual = BalanceBase(data).total_row

    assert actual == expected


def test_total_column(df):
    actual = BalanceBase(df).total_column

    expect = [
        {"date": date(1999, 1, 1), "total": 32},
        {"date": date(1999, 1, 2), "total": 32},
        {"date": date(1999, 1, 3), "total": 21},
        {"date": date(1999, 1, 4), "total": 11},
    ]

    assert actual == expect


@pytest.mark.parametrize("data, expect", [(None, []), (pl.DataFrame(), [])])
def test_total_column_empty_data(data, expect):
    actual = BalanceBase(data).total_column

    assert actual == expect


@pytest.mark.parametrize("data, expect", [(ARR, 96), (None, 0), (pl.DataFrame(), 0)])
def test_total(data, expect):
    actual = BalanceBase(data).total

    assert actual == expect


def test_types(df):
    actual = BalanceBase(df).types

    assert actual == ["x", "y"]
