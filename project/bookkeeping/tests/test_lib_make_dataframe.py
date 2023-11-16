from datetime import date

import polars as pl
import pytest

from ..lib import make_dataframe


@pytest.fixture(name="month_data")
def fixture_month_data():
    return [
        {
            "date": date(1999, 1, 1),
            "title": "T1",
            "sum": 4,
            "exception_sum": 3,
        },
        {
            "date": date(1999, 1, 1),
            "title": "T2",
            "sum": 2,
            "exception_sum": 0,
        },
        {
            "date": date(1999, 1, 1),
            "title": "T1",
            "sum": 3,
            "exception_sum": 0,
        },
        {
            "date": date(1999, 12, 1),
            "title": "T1",
            "sum": 4,
            "exception_sum": 0,
        },
        {
            "date": date(1999, 12, 1),
            "title": "T2",
            "sum": 5,
            "exception_sum": 0,
        },
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


def test_month_expenses(month_data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, data=month_data, columns=columns
    ).data

    assert actual.shape == (12, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]

    # 1999-01-01 first row
    assert actual[0, "T0"] == 0.0
    assert actual[0, "T1"] == 4.0
    assert actual[0, "T2"] == 2.0

    # 1999-12-01 last row
    assert actual[11, "T0"] == 0.0
    assert actual[11, "T1"] == 4.0
    assert actual[11, "T2"] == 5.0


def test_month_expenses(month_data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, data=month_data, columns=columns
    ).data

    assert actual.shape == (12, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]

    # 1999-01-01 first row
    assert actual[0, "T0"] == 0.0
    assert actual[0, "T1"] == 4.0
    assert actual[0, "T2"] == 2.0

    # 1999-12-01 last row
    assert actual[11, "T0"] == 0.0
    assert actual[11, "T1"] == 4.0
    assert actual[11, "T2"] == 5.0


def test_month_expenses_partial_data():
    data = [
        {"date": date(1999, 2, 1), "title": "X", "sum": 5},
    ]

    actual = make_dataframe.MakeDataFrame(
        year=1999, data=data).data

    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "X"]


def test_month_no_data_expenses(columns):
    actual = make_dataframe.MakeDataFrame(year=1999, data=[], columns=columns).data

    for i in range(12):
        assert actual[i, "T0"] == 0.0
        assert actual[i, "T1"] == 0.0
        assert actual[i, "T2"] == 0.0


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
    actual = make_dataframe.MakeDataFrame(
        year=1999, data=month_data, columns=columns
    ).data

    assert actual.dtypes[2] == pl.Int32  # T1
    assert actual.dtypes[3] == pl.Int32  # T2


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_month_no_data_and_no_columns_expenses(data, columns):
    actual = make_dataframe.MakeDataFrame(year=1999, data=data, columns=columns).data

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (12, 1)
    assert actual.columns == ["date"]


def test_month_exceptions(month_data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, data=month_data, columns=columns
    ).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "sum"]
    assert actual[0, "sum"] == 3


@pytest.mark.parametrize("data", [([]), (None)])
def test_month_no_data_exceptions(data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, data=data, columns=columns
    ).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "sum"]


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_month_no_data_and_no_columns_exceptions(data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, data=data, columns=columns
    ).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (12, 2)
    assert actual.columns == ["date", "sum"]


def test_day_expenses(day_data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, month=1, data=day_data, columns=columns
    ).data

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]

    # first row 1999-01-01
    assert actual[0, "T0"] == 0.0
    assert actual[0, "T1"] == 5.0
    assert actual[0, "T2"] == 2.0

    # last row 1999-01-30
    assert actual[29, "T0"] == 0.0
    assert actual[29, "T1"] == 3.0
    assert actual[29, "T2"] == 0.0


@pytest.mark.parametrize("data", [([]), (None)])
def test_day_no_data_expenses(data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, month=1, data=data, columns=columns
    ).data

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 4)
    assert actual.columns == ["date", "T0", "T1", "T2"]


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_day_no_data_and_no_columns_expenses(data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, month=1, data=data, columns=columns
    ).data

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 1)
    assert actual.columns == ["date"]


def test_day_exceptions(day_data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, month=1, data=day_data, columns=columns
    ).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 2)
    assert actual[0, "sum"] == 4


@pytest.mark.parametrize("data", [([]), (None)])
def test_day_no_data_exceptions(data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, month=1, data=data, columns=columns
    ).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 2)
    assert actual.columns == ["date", "sum"]

    actual = actual.select(pl.col("sum").sum()).row(0)
    assert actual == (0.0,)


@pytest.mark.parametrize("data, columns", [([], []), (None, None)])
def test_day_no_data_and_no_columns_exceptions(data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, month=1, data=data, columns=columns
    ).exceptions

    assert isinstance(actual, pl.DataFrame)
    assert actual.shape == (31, 2)
    assert actual.columns == ["date", "sum"]


def test_expenses_and_exceptions_same_size(month_data, columns):
    actual = make_dataframe.MakeDataFrame(
        year=1999, month=1, data=month_data, columns=columns
    )

    assert actual.exceptions.shape[0] == actual.data.shape[0]


def test_transform_year_no_data():
    actual = make_dataframe.MakeDataFrame(year=1999, data=[])._modify_data()

    assert len(actual) == 12
    assert actual[0] == {
        "date": date(1999, 1, 1),
        "title": "__tmp_to_drop__",
        "sum": 0,
        "exception_sum": 0,
    }
    assert actual[11] == {
        "date": date(1999, 12, 1),
        "title": "__tmp_to_drop__",
        "sum": 0,
        "exception_sum": 0,
    }


def test_transform_year_data_no_exeptions():
    data = [
        {"date": date(1999, 2, 1), "title": "X", "sum": 5},
        {"date": date(1999, 3, 1), "title": "Y", "sum": 5},
    ]

    actual = make_dataframe.MakeDataFrame(year=1999, data=data)._modify_data()

    assert len(actual) == 26
    assert actual[2] == {"date": date(1999, 1, 1), "title": "X", "sum": 0}
    assert actual[13] == {"date": date(1999, 12, 1), "title": "X", "sum": 0}
    assert actual[14] == {"date": date(1999, 1, 1), "title": "Y", "sum": 0}
    assert actual[25] == {"date": date(1999, 12, 1), "title": "Y", "sum": 0}


def test_transform_year_data_with_exeptions():
    data = [
        {"date": date(1999, 2, 1), "title": "X", "sum": 5, "exception_sum": 4},
        {"date": date(1999, 3, 1), "title": "Y", "sum": 6, "exception_sum": 44},
    ]

    actual = make_dataframe.MakeDataFrame(year=1999, data=data)._modify_data()

    assert len(actual) == 26
    assert actual[2] == {
        "date": date(1999, 1, 1),
        "title": "X",
        "sum": 0,
        "exception_sum": 0,
    }
    assert actual[13] == {
        "date": date(1999, 12, 1),
        "title": "X",
        "sum": 0,
        "exception_sum": 0,
    }
    assert actual[14] == {
        "date": date(1999, 1, 1),
        "title": "Y",
        "sum": 0,
        "exception_sum": 0,
    }
    assert actual[25] == {
        "date": date(1999, 12, 1),
        "title": "Y",
        "sum": 0,
        "exception_sum": 0,
    }


def test_transform_month_no_data():
    actual = make_dataframe.MakeDataFrame(year=1999, month=1, data=[])._modify_data()

    assert len(actual) == 31
    assert actual[0] == {
        "date": date(1999, 1, 1),
        "title": "__tmp_to_drop__",
        "sum": 0,
        "exception_sum": 0,
    }
    assert actual[30] == {
        "date": date(1999, 1, 31),
        "title": "__tmp_to_drop__",
        "sum": 0,
        "exception_sum": 0,
    }


def test_transform_month_data_no_exeptions():
    data = [
        {"date": date(1999, 1, 2), "title": "X", "sum": 5},
        {"date": date(1999, 1, 1), "title": "Y", "sum": 5},
    ]

    actual = make_dataframe.MakeDataFrame(year=1999, month=1, data=data)._modify_data()

    assert len(actual) == 64
    assert actual[2] == {"date": date(1999, 1, 1), "title": "X", "sum": 0}
    assert actual[32] == {"date": date(1999, 1, 31), "title": "X", "sum": 0}
    assert actual[33] == {"date": date(1999, 1, 1), "title": "Y", "sum": 0}
    assert actual[63] == {"date": date(1999, 1, 31), "title": "Y", "sum": 0}


def test_transform_month_data_with_exeptions():
    data = [
        {"date": date(1999, 2, 1), "title": "X", "sum": 5, "exception_sum": 4},
        {"date": date(1999, 3, 1), "title": "Y", "sum": 6, "exception_sum": 44},
    ]

    actual = make_dataframe.MakeDataFrame(year=1999, month=1, data=data)._modify_data()

    assert len(actual) == 64
    assert actual[2] == {
        "date": date(1999, 1, 1),
        "title": "X",
        "sum": 0,
        "exception_sum": 0,
    }
    assert actual[32] == {
        "date": date(1999, 1, 31),
        "title": "X",
        "sum": 0,
        "exception_sum": 0,
    }
    assert actual[33] == {
        "date": date(1999, 1, 1),
        "title": "Y",
        "sum": 0,
        "exception_sum": 0,
    }
    assert actual[63] == {
        "date": date(1999, 1, 31),
        "title": "Y",
        "sum": 0,
        "exception_sum": 0,
    }
