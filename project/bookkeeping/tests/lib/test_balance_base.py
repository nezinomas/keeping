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


MONTHS = pl.DataFrame(
    {
        "date": [date(1999, month, 1) for month in (1, 2, 3, 4)],
        "x": [11, None, 0, 22],
        "y": [21, 21, 21, 0],
    }
)


@pytest.mark.parametrize(
    "data, months, expected",
    [
        pytest.param(MONTHS, 4, {"x": 8.25, "y": 15.75}, id="empty-months-count"),
        pytest.param(MONTHS, 1, {"x": 11, "y": 21}, id="later-months-left-out"),
        pytest.param(MONTHS, 0, {"x": 0, "y": 0}, id="year-not-begun"),
        pytest.param(MONTHS.select("date"), 4, {}, id="dates-alone"),
        pytest.param(pl.DataFrame(), 4, {}, id="empty"),
    ],
)
def test_average_over_divides_each_columns_sum_to_a_month_by_those_months(
    data, months, expected
):
    actual = BalanceBase(data).average_over(months)

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
