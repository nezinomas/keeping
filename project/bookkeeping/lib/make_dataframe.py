import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import cached_property

import polars as pl

from ...core.lib.table_columns import DATE


def _date_frame(dates: list[date]) -> pl.DataFrame:
    return pl.DataFrame({DATE: dates}).with_columns(pl.col(DATE).cast(pl.Date))


@dataclass(frozen=True)
class YearMonths:
    year: int

    def dates(self) -> pl.DataFrame:
        return _date_frame([date(self.year, m, 1) for m in range(1, 13)])


@dataclass(frozen=True)
class MonthDays:
    year: int
    month: int

    def dates(self) -> pl.DataFrame:
        days = calendar.monthrange(self.year, self.month)[1]
        return _date_frame([date(self.year, self.month, d) for d in range(1, days + 1)])


class DataFrameSchemaFormatter:
    """Handles enforcing required columns and sorting them alphabetically."""

    def __init__(self, required_columns: Sequence[str]):
        self.required_columns = tuple(required_columns)

    def format(self, df: pl.DataFrame) -> pl.DataFrame:
        missing_cols = [
            pl.lit(0).cast(pl.Int32).alias(col)
            for col in self.required_columns
            if col not in df.columns
        ]

        if missing_cols:
            df = df.with_columns(missing_cols)

        data_cols = sorted([col for col in df.columns if col != DATE])
        return df.select([DATE, *data_cols])


class TimeSeriesPivotBuilder:
    """Transforms raw dictionary data into a padded, clean Polars pivot table."""

    def __init__(self, date_range: YearMonths | MonthDays, columns: Sequence[str]):
        self.date_range = date_range
        self.formatter = DataFrameSchemaFormatter(columns)

    def build(self, raw_data: list[dict], value_column: str) -> pl.DataFrame:
        return self.formatter.format(self._padded(raw_data, value_column))

    def _padded(self, raw_data: list[dict], value_column: str) -> pl.DataFrame:
        expected_dates_df = self.date_range.dates()
        df = pl.DataFrame(raw_data)

        if value_column not in df.columns:
            return expected_dates_df

        pivoted_df = (
            df.group_by([DATE, "title"])
            .agg(pl.col(value_column).sum().cast(pl.Int32))
            .pivot(
                index=DATE,
                on="title",
                values=value_column,
                aggregate_function="first",
            )
        )

        return (
            expected_dates_df.join(pivoted_df, on=DATE, how="left")
            .fill_null(0)
            .sort(DATE)
        )


class MakeDataFrame:
    def __init__(
        self,
        date_range: YearMonths | MonthDays,
        data: list[dict],
        columns: Sequence[str],
    ):
        self.date_range = date_range
        self._data = data

        self._builder = TimeSeriesPivotBuilder(date_range, columns)

    @classmethod
    def for_year(
        cls, year: int, data: list[dict], columns: Sequence[str] = ()
    ) -> "MakeDataFrame":
        return cls(YearMonths(year), data, columns)

    @classmethod
    def for_month(
        cls, year: int, month: int, data: list[dict], columns: Sequence[str] = ()
    ) -> "MakeDataFrame":
        return cls(MonthDays(year, month), data, columns)

    @cached_property
    def data(self) -> pl.DataFrame:
        return self._builder.build(self._data, value_column="sum")

    @cached_property
    def exceptions(self) -> pl.DataFrame:
        df = self._builder.build(self._data, value_column="exception_sum")

        if len(df.columns) <= 1:
            return df.with_columns(sum=pl.lit(0).cast(pl.Int32))

        return df.select(
            [pl.col(DATE), pl.sum_horizontal(pl.exclude(DATE)).alias("sum")]
        )
