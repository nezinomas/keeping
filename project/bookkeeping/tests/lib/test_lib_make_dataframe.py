from datetime import date

import polars as pl
import pytest

from ...lib.make_dataframe import (
    DataFrameSchemaFormatter,
    MakeDataFrame,
    MonthDays,
    TimeSeriesPivotBuilder,
    YearMonths,
)


@pytest.fixture(name="month_data")
def fixture_month_data():
    return [
        {"date": date(1999, 1, 1), "title": "T1", "sum": 4, "exception_sum": 3},
        {"date": date(1999, 1, 1), "title": "T2", "sum": 2, "exception_sum": 0},
        {"date": date(1999, 1, 1), "title": "T1", "sum": 3, "exception_sum": 0},
        {"date": date(1999, 12, 1), "title": "T1", "sum": 4, "exception_sum": 0},
        {"date": date(1999, 12, 1), "title": "T2", "sum": 5, "exception_sum": 0},
    ]


@pytest.fixture(name="columns")
def fixture_columns():
    return ["T1", "T2", "T0"]


def test_year_months():
    actual = YearMonths(1999).dates()
    assert actual.shape == (12, 1)
    assert actual.columns == ["date"]
    assert actual[0, "date"] == date(1999, 1, 1)
    assert actual[11, "date"] == date(1999, 12, 1)
    assert actual.dtypes[0] == pl.Date


@pytest.mark.parametrize(
    "year, month, expected_days, expected_last_date",
    [
        pytest.param(1999, 1, 31, date(1999, 1, 31), id="31_days"),
        pytest.param(1999, 4, 30, date(1999, 4, 30), id="30_days"),
        pytest.param(1999, 2, 28, date(1999, 2, 28), id="february"),
        pytest.param(2000, 2, 29, date(2000, 2, 29), id="leap_february"),
    ],
)
def test_month_days_variations(year, month, expected_days, expected_last_date):
    actual = MonthDays(year, month).dates()
    assert actual.shape == (expected_days, 1)
    assert actual[0, "date"] == date(year, month, 1)
    assert actual[-1, "date"] == expected_last_date


def test_schema_formatter_adds_missing_columns():
    df = pl.DataFrame({"date": [date(1999, 1, 1)], "T1": [10]})
    formatter = DataFrameSchemaFormatter(required_columns=["T1", "T2", "T0"])

    actual = formatter.format(df)

    assert actual.columns == ["date", "T0", "T1", "T2"]
    assert actual[0, "T0"] == 0
    assert actual[0, "T2"] == 0
    assert actual.dtypes[actual.columns.index("T0")] == pl.Int32


def test_schema_formatter_sorts_alphabetically_with_date_first():
    df = pl.DataFrame({"Z": [1], "date": [date(1999, 1, 1)], "A": [2], "M": [3]})
    formatter = DataFrameSchemaFormatter(required_columns=())

    actual = formatter.format(df)
    assert actual.columns == ["date", "A", "M", "Z"]


def test_schema_formatter_handles_empty_dataframe():
    df = pl.DataFrame({"date": [], "X": []})
    formatter = DataFrameSchemaFormatter(required_columns=["Y"])

    actual = formatter.format(df)
    assert actual.columns == ["date", "X", "Y"]
    assert actual.shape == (0, 3)


def test_pivot_builder_standard_data(month_data, columns):
    builder = TimeSeriesPivotBuilder(YearMonths(1999), columns=columns)
    actual = builder.build(month_data, value_column="sum")

    assert actual.shape == (12, 4)
    assert actual[0, "T1"] == 7
    assert actual[0, "T2"] == 2
    assert actual[11, "T1"] == 4
    assert actual[11, "T2"] == 5


def test_pivot_builder_empty_data_returns_zeroed_spine(columns):
    builder = TimeSeriesPivotBuilder(YearMonths(1999), columns=columns)
    actual = builder.build([], value_column="sum")

    assert actual.shape == (12, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]
    assert sum(actual["T1"].to_list()) == 0


def test_pivot_builder_missing_value_column_returns_zeroed_spine():
    data = [{"date": date(1999, 1, 1), "title": "T1", "sum": 5}]
    builder = TimeSeriesPivotBuilder(YearMonths(1999), columns=["T1"])

    actual = builder.build(data, value_column="exception_sum")

    assert actual.shape == (12, 2)
    assert sum(actual["T1"].to_list()) == 0


def test_facade_month_expenses_partial_data():
    data = [{"date": date(1999, 2, 1), "title": "X", "sum": 5}]
    actual = MakeDataFrame.for_year(year=1999, data=data).data
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "X"]


@pytest.mark.parametrize(
    "facade, rows",
    [
        pytest.param(lambda: MakeDataFrame.for_year(1999, []), 12, id="year"),
        pytest.param(lambda: MakeDataFrame.for_month(1999, 2, []), 28, id="month"),
    ],
)
def test_facade_without_columns_is_dates_alone(facade, rows):
    actual = facade().data
    assert actual.shape == (rows, 1)
    assert actual.columns == ["date"]


@pytest.mark.parametrize(
    "data, columns, first_month",
    [
        pytest.param(
            [
                {"date": date(1999, 1, 1), "title": "T1", "sum": 4, "exception_sum": 3},
                {"date": date(1999, 1, 1), "title": "T2", "sum": 2, "exception_sum": 2},
                {
                    "date": date(1999, 12, 1),
                    "title": "T1",
                    "sum": 4,
                    "exception_sum": 0,
                },
            ],
            ["T1", "T2", "T0"],
            5,
            id="with_data",
        ),
        pytest.param(
            [{"date": date(1999, 1, 1), "title": "T1", "sum": 4, "exception_sum": 3}],
            [],
            3,
            id="one_title",
        ),
        pytest.param([], [], 0, id="no_data"),
    ],
)
def test_facade_exceptions(data, columns, first_month):
    actual = MakeDataFrame.for_year(year=1999, data=data, columns=columns).exceptions
    assert actual.columns == ["date", "sum"]
    assert actual["sum"].to_list() == [first_month] + [0] * 11
