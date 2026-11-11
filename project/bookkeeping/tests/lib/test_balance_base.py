from datetime import date

import polars as pl
import pytest

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
    "before",
    [
        pytest.param(lambda obj: None, id="alone"),
        pytest.param(lambda obj: obj.total_row, id="after-total-row"),
    ],
)
@pytest.mark.parametrize(
    "df, expected",
    [
        (None, []),
        (pl.DataFrame(), []),
        (pl.DataFrame({"t": [11], "date": ["x"]}), [{"t": 11, "date": "x"}]),
    ],
)
def test_balance(before, df, expected):
    obj = BalanceBase(df)

    before(obj)

    assert obj.balance == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        pytest.param(ARR, {"x": 11, "y": 21}, id="zero-months-not-counted"),
        pytest.param(pl.DataFrame({"x": [11, 22]}), {"x": 16.5}, id="all-months"),
        pytest.param(
            pl.DataFrame({"x": [0, 11, 0, 22]}), {"x": 16.5}, id="zeros-skipped"
        ),
        pytest.param(
            pl.DataFrame({"x": [None, 11, 22]}), {"x": 16.5}, id="null-skipped"
        ),
        pytest.param(
            pl.DataFrame({"x": pl.Series([0, None], dtype=pl.Float32)}),
            {"x": 0},
            id="no-value",
        ),
        pytest.param(
            pl.DataFrame({"t1": [11, 22], "t2": [0, 0]}),
            {"t1": 16.5, "t2": 0},
            id="all-zero-column",
        ),
        pytest.param(pl.DataFrame(), {}, id="empty"),
        pytest.param(None, {}, id="none"),
    ],
)
def test_average_is_the_mean_of_each_column_over_its_months_with_a_value(
    data, expected
):
    actual = BalanceBase(data).average

    assert actual == pytest.approx(expected)


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


@pytest.mark.parametrize(
    "data, expect",
    [
        (
            ARR,
            [
                {"date": date(1999, 1, 1), "total": 32},
                {"date": date(1999, 1, 2), "total": 32},
                {"date": date(1999, 1, 3), "total": 21},
                {"date": date(1999, 1, 4), "total": 11},
            ],
        ),
        (None, []),
        (pl.DataFrame(), []),
    ],
)
def test_total_column(data, expect):
    actual = BalanceBase(data).total_column

    assert actual == expect


@pytest.mark.parametrize("data, expect", [(ARR, 96), (None, 0), (pl.DataFrame(), 0)])
def test_total(data, expect):
    actual = BalanceBase(data).total

    assert actual == expect


def test_types(df):
    actual = BalanceBase(df).types

    assert actual == ["x", "y"]
