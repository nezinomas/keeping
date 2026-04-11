from datetime import date

import polars as pl
import pytest

from ...lib.make_dataframe import (
    DataFrameSchemaFormatter,
    DateRangeProvider,
    MakeDataFrame,
    TimeSeriesPivotBuilder,
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


@pytest.fixture(name="day_data")
def fixture_day_data():
    return [
        {"date": date(1999, 1, 1), "title": "T1", "sum": 5, "exception_sum": 4},
        {"date": date(1999, 1, 1), "title": "T2", "sum": 2, "exception_sum": 0},
        {"date": date(1999, 1, 30), "title": "T1", "sum": 3, "exception_sum": 0},
    ]


@pytest.fixture(name="columns")
def fixture_columns():
    return ["T1", "T2", "T0"]


def test_date_range_provider_year():
    actual = DateRangeProvider.get_dates(1999)
    assert actual.shape == (12, 1)
    assert actual.columns == ["date"]
    assert actual[0, "date"] == date(1999, 1, 1)
    assert actual[11, "date"] == date(1999, 12, 1)
    assert actual.dtypes[0] == pl.Date


@pytest.mark.parametrize(
    "year, month, expected_days, expected_last_date",
    [
        (1999, 1, 31, date(1999, 1, 31)),  # Standard 31-day month
        (1999, 4, 30, date(1999, 4, 30)),  # Standard 30-day month
        (1999, 2, 28, date(1999, 2, 28)),  # Non-leap year February
        (2000, 2, 29, date(2000, 2, 29)),  # Leap year February
    ],
)
def test_date_range_provider_month_variations(
    year, month, expected_days, expected_last_date
):
    actual = DateRangeProvider.get_dates(year, month)
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
    formatter = DataFrameSchemaFormatter()  # No required columns

    actual = formatter.format(df)
    assert actual.columns == ["date", "A", "M", "Z"]


def test_schema_formatter_handles_empty_dataframe():
    df = pl.DataFrame({"date": [], "X": []})
    formatter = DataFrameSchemaFormatter(required_columns=["Y"])

    actual = formatter.format(df)
    assert actual.columns == ["date", "X", "Y"]
    assert actual.shape == (0, 3)


def test_pivot_builder_standard_data(month_data, columns):
    builder = TimeSeriesPivotBuilder(year=1999, columns=columns)
    actual = builder.build(month_data, value_column="sum")

    assert actual.shape == (12, 4)
    assert actual[0, "T1"] == 7  # 4 + 3 (grouped and summed)
    assert actual[0, "T2"] == 2
    assert actual[11, "T1"] == 4
    assert actual[11, "T2"] == 5


def test_pivot_builder_empty_data_returns_zeroed_spine(columns):
    builder = TimeSeriesPivotBuilder(year=1999, columns=columns)
    actual = builder.build([], value_column="sum")

    assert actual.shape == (12, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]
    assert sum(actual["T1"].to_list()) == 0


def test_pivot_builder_missing_value_column_returns_zeroed_spine():
    data = [{"date": date(1999, 1, 1), "title": "T1", "sum": 5}]
    builder = TimeSeriesPivotBuilder(year=1999, columns=["T1"])

    actual = builder.build(data, value_column="exception_sum")

    assert actual.shape == (12, 2)
    assert sum(actual["T1"].to_list()) == 0


def test_facade_month_expenses(month_data, columns):
    actual = MakeDataFrame(year=1999, data=month_data, columns=columns).data
    assert actual.shape == (12, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]
    assert actual[0, "T1"] == 7


def test_facade_month_expenses_partial_data():
    data = [{"date": date(1999, 2, 1), "title": "X", "sum": 5}]
    actual = MakeDataFrame(year=1999, data=data).data
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "X"]


def test_facade_month_no_data_expenses(columns):
    actual = MakeDataFrame(year=1999, data=[], columns=columns).data
    assert actual.select(pl.sum_horizontal(pl.exclude("date")).sum()).item() == 0


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_facade_month_no_data_and_no_columns_expenses(data, columns):
    actual = MakeDataFrame(year=1999, data=data, columns=columns).data
    assert actual.shape == (12, 1)
    assert actual.columns == ["date"]


def test_facade_month_exceptions(month_data, columns):
    actual = MakeDataFrame(year=1999, data=month_data, columns=columns).exceptions
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "sum"]
    assert actual[0, "sum"] == 3


@pytest.mark.parametrize("data", [([]), (None)])
def test_facade_month_no_data_exceptions(data, columns):
    actual = MakeDataFrame(year=1999, data=data, columns=columns).exceptions
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "sum"]
    assert actual.select(pl.col("sum").sum()).item() == 0


def test_facade_day_expenses(day_data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=day_data, columns=columns).data
    assert actual.shape == (31, 4)
    assert actual[0, "T1"] == 5
    assert actual[29, "T1"] == 3


@pytest.mark.parametrize("data", [([]), (None)])
def test_facade_day_no_data_exceptions(data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=data, columns=columns).exceptions
    assert actual.shape == (31, 2)
    assert actual.columns == ["date", "sum"]
    assert actual.select(pl.col("sum").sum()).item() == 0


def test_facade_expenses_and_exceptions_same_size(month_data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=month_data, columns=columns)
    assert actual.exceptions.shape[0] == actual.data.shape[0]


def test_facade_preserves_public_attributes():
    actual = MakeDataFrame(year=1999, month=5, data=[], columns=["T1"])
    assert actual.year == 1999
    assert actual.month == 5
