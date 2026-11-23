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
    "read, expect",
    [
        pytest.param(lambda b: b.total_row, {"x": 33, "y": 63}, id="total-row"),
        pytest.param(
            lambda b: b.total_column,
            [
                {"date": date(1999, 1, 1), "total": 32},
                {"date": date(1999, 1, 2), "total": 32},
                {"date": date(1999, 1, 3), "total": 21},
                {"date": date(1999, 1, 4), "total": 11},
            ],
            id="total-column",
        ),
        pytest.param(lambda b: b.total, 96, id="total"),
        pytest.param(lambda b: b.types, ["x", "y"], id="types"),
    ],
)
def test_each_figure_of_a_frame(read, expect):
    assert read(BalanceBase(ARR)) == expect


@pytest.mark.parametrize(
    "read, expect",
    [
        pytest.param(lambda b: b.total_row, {}, id="total-row"),
        pytest.param(lambda b: b.total_column, [], id="total-column"),
        pytest.param(lambda b: b.total, 0, id="total"),
    ],
)
def test_an_empty_frame_has_no_total_row_column_or_sum(read, expect):
    assert read(BalanceBase(pl.DataFrame())) == expect
