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
    """Replaces old _modify_data tests to ensure a 12-month spine is created."""
    actual = DateRangeProvider.get_dates(1999)
    assert actual.shape == (12, 1)
    assert actual.columns == ["date"]
    assert actual[0, "date"] == date(1999, 1, 1)
    assert actual[11, "date"] == date(1999, 12, 1)


def test_date_range_provider_month():
    """Replaces old _modify_data tests to ensure a full month spine is created."""
    actual = DateRangeProvider.get_dates(1999, 2)  # February 1999 has 28 days
    assert actual.shape == (28, 1)
    assert actual[0, "date"] == date(1999, 2, 1)
    assert actual[27, "date"] == date(1999, 2, 28)


def test_schema_formatter_adds_missing_and_sorts():
    df = pl.DataFrame({"date": [date(1999, 1, 1)], "Z": [10], "A": [5]})
    formatter = DataFrameSchemaFormatter(required_columns=["X", "Y", "A"])

    actual = formatter.format(df)

    # "date" must be first, the rest alphabetical: A, X, Y, Z
    assert actual.columns == ["date", "A", "X", "Y", "Z"]

    # Check that missing columns were filled with 0 and cast to Int32
    assert actual[0, "X"] == 0
    assert actual.dtypes[actual.columns.index("X")] == pl.Int32


def test_month_expenses(month_data, columns):
    actual = MakeDataFrame(year=1999, data=month_data, columns=columns).data

    assert actual.shape == (12, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]

    # 1999-01-01 first row
    assert actual[0, "T0"] == 0
    assert actual[0, "T1"] == 7
    assert actual[0, "T2"] == 2

    # 1999-12-01 last row
    assert actual[11, "T0"] == 0
    assert actual[11, "T1"] == 4
    assert actual[11, "T2"] == 5


def test_month_expenses_partial_data():
    data = [{"date": date(1999, 2, 1), "title": "X", "sum": 5}]
    actual = MakeDataFrame(year=1999, data=data).data

    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "X"]


def test_month_no_data_expenses(columns):
    actual = MakeDataFrame(year=1999, data=[], columns=columns).data

    for i in range(12):
        assert actual[i, "T0"] == 0
        assert actual[i, "T1"] == 0
        assert actual[i, "T2"] == 0


def test_month_dtype(month_data, columns):
    for i in range(2, 12):
        month_data.extend(
            [
                {
                    "date": date(1999, i, 1),
                    "title": "T1",
                    "sum": 11,
                    "exception_sum": 5,
                },
            ]
        )
    actual = MakeDataFrame(year=1999, data=month_data, columns=columns).data

    assert actual.dtypes[2] == pl.Int32  # T1
    assert actual.dtypes[3] == pl.Int32  # T2


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_month_no_data_and_no_columns_expenses(data, columns):
    actual = MakeDataFrame(year=1999, data=data, columns=columns).data

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (12, 1)
    assert actual.columns == ["date"]


def test_month_exceptions(month_data, columns):
    actual = MakeDataFrame(year=1999, data=month_data, columns=columns).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "sum"]
    assert actual[0, "sum"] == 3


@pytest.mark.parametrize("data", [([]), (None)])
def test_month_no_data_exceptions(data, columns):
    actual = MakeDataFrame(year=1999, data=data, columns=columns).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "sum"]


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_month_no_data_and_no_columns_exceptions(data, columns):
    actual = MakeDataFrame(year=1999, data=data, columns=columns).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "sum"]


def test_day_expenses(day_data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=day_data, columns=columns).data

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]

    # first row 1999-01-01
    assert actual[0, "T0"] == 0
    assert actual[0, "T1"] == 5
    assert actual[0, "T2"] == 2

    # last row 1999-01-30
    assert actual[29, "T0"] == 0
    assert actual[29, "T1"] == 3
    assert actual[29, "T2"] == 0


@pytest.mark.parametrize("data", [([]), (None)])
def test_day_no_data_expenses(data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=data, columns=columns).data

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_day_no_data_and_no_columns_expenses(data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=data, columns=columns).data

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 1)
    assert actual.columns == ["date"]


def test_day_exceptions(day_data, columns):
    actual = MakeDataFrame(
        year=1999, month=1, data=day_data, columns=columns
    ).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 2)
    assert actual[0, "sum"] == 4


@pytest.mark.parametrize("data", [([]), (None)])
def test_day_no_data_exceptions(data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=data, columns=columns).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 2)
    assert actual.columns == ["date", "sum"]

    actual = actual.select(pl.col("sum").sum()).row(0)
    assert actual == (0,)


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_day_no_data_and_no_columns_exceptions(data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=data, columns=columns).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 2)
    assert actual.columns == ["date", "sum"]


def test_expenses_and_exceptions_same_size(month_data, columns):
    actual = MakeDataFrame(year=1999, month=1, data=month_data, columns=columns)

    assert actual.exceptions.shape[0] == actual.data.shape[0]
