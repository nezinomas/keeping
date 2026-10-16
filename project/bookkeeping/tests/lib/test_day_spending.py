from datetime import date
from types import SimpleNamespace

import polars as pl
import pytest

from ...lib.day_spending import DaySpending
from ...lib.make_dataframe import MakeDataFrame, MonthDays

TODAY = date(1999, 1, 2)


@pytest.fixture(name="df")
def fixture_df():
    exp = [
        {"date": date(1999, 1, 1), "N": 999, "O1": 10, "O2": 125},
        {"date": date(1999, 1, 2), "N": 999, "O1": 0, "O2": 105},
        {"date": date(1999, 1, 3), "N": 999, "O1": 0, "O2": 0},
    ]
    exp = pl.DataFrame(exp)

    exc = [
        {"date": date(1999, 1, 1), "sum": 10},
        {"date": date(1999, 1, 2), "sum": 0},
        {"date": date(1999, 1, 3), "sum": 0},
    ]
    exc = pl.DataFrame(exc)

    return SimpleNamespace(data=exp, exceptions=exc, date_range=MonthDays(1999, 1))


@pytest.fixture(name="necessary")
def fixture_necessary():
    return ["N"]


@pytest.fixture(name="sparse_month")
def fixture_sparse_month():
    days = [date(1999, 1, 1), date(1999, 1, 2), date(1999, 1, 3), date(1999, 1, 31)]
    return SimpleNamespace(
        data=pl.DataFrame({"date": days, "O": [11, 21, 31, 41]}),
        exceptions=pl.DataFrame({"date": days, "sum": [0, 0, 0, 0]}),
        date_range=MonthDays(1999, 1),
    )


def test_avg_per_day(df, necessary):
    obj = DaySpending(
        expense=df,
        necessary=necessary,
        per_day=25,
        free=200,
        today=TODAY,
    )

    actual = obj.avg_per_day

    assert 115 == actual


@pytest.mark.parametrize(
    "index, day_date, day, full",
    [
        pytest.param(0, date(1999, 1, 1), -100, -100, id="first_day"),
        pytest.param(1, date(1999, 1, 2), -80, -180, id="second_day"),
    ],
)
def test_spending_day_and_full_leave_out_necessary_and_exceptions(
    df, necessary, index, day_date, day, full
):
    obj = DaySpending(
        expense=df,
        necessary=necessary,
        per_day=25,
        free=200,
        today=TODAY,
    )

    actual = obj.spending

    assert actual[index]["date"] == day_date
    assert actual[index]["day"] == day
    assert actual[index]["full"] == full


@pytest.mark.parametrize(
    "per_day, free, expect",
    [
        pytest.param(25, 200, -1099, id="first_day_necessary_empty"),
        pytest.param(0, 0, -1124, id="first_day_all_empty"),
    ],
)
def test_spending_first_day_without_necessary(df, per_day, free, expect):
    obj = DaySpending(
        expense=df,
        necessary=[],
        per_day=per_day,
        free=free,
        today=TODAY,
    )

    actual = obj.spending

    assert actual[0]["date"] == date(1999, 1, 1)
    assert actual[0]["day"] == expect
    assert actual[0]["full"] == expect


def test_spending_balance_expenses_empty():
    obj = DaySpending(
        expense=SimpleNamespace(
            data=pl.DataFrame(),
            exceptions=pl.DataFrame(),
            date_range=MonthDays(1999, 1),
        ),
        necessary=[],
        per_day=0,
        free=0,
        today=TODAY,
    )

    assert obj.spending == []


@pytest.mark.parametrize(
    "today, expect",
    [
        pytest.param(date(1999, 1, 2), 16, id="average_month_two_days"),
        pytest.param(date(1999, 1, 31), 3.35, id="average_month_last_day"),
        pytest.param(date(1974, 1, 1), 3.35, id="average_month_other_year"),
    ],
)
def test_average_month_over_the_days_reached(sparse_month, today, expect):
    obj = DaySpending(
        expense=sparse_month, necessary=[], per_day=0, free=0, today=today
    )
    actual = obj.avg_per_day

    assert round(actual, 2) == expect


def test_average_month_empty_dataframe():
    obj = DaySpending(
        expense=SimpleNamespace(
            data=pl.DataFrame(),
            exceptions=pl.DataFrame(),
            date_range=MonthDays(1999, 1),
        ),
        necessary=[],
        per_day=0,
        free=0,
        today=TODAY,
    )

    assert obj.avg_per_day == 0


def test_spending_reads_the_month_named_by_caller():
    rows = [
        {"date": date(1999, 1, 1), "title": "N", "sum": 999, "exception_sum": 0},
        {"date": date(1999, 1, 1), "title": "O", "sum": 125, "exception_sum": 10},
        {"date": date(1999, 1, 2), "title": "O", "sum": 105, "exception_sum": 0},
    ]
    frame = MakeDataFrame.for_month(1999, 1, rows, columns=["N", "O"])

    obj = DaySpending(
        expense=frame,
        necessary=["N"],
        per_day=25,
        free=200,
        today=TODAY,
    )

    first, second = obj.spending[:2]
    assert (first["day"], first["real"], first["full"]) == (-90, 85, -90)
    assert (second["day"], second["real"], second["full"]) == (-80, -20, -170)
    assert obj.avg_per_day == 110


def test_spending_refuses_a_year_frame():
    rows = [{"date": date(1999, 1, 1), "title": "O", "sum": 125, "exception_sum": 10}]
    frame = MakeDataFrame.for_year(1999, rows, columns=["O"])

    with pytest.raises(TypeError, match="month frame"):
        DaySpending(expense=frame, necessary=[], per_day=25, free=200, today=TODAY)
