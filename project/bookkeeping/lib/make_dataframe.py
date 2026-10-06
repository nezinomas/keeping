import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import polars as pl


def _date_frame(dates: list[date]) -> pl.DataFrame:
    return pl.DataFrame({"date": dates}).with_columns(pl.col("date").cast(pl.Date))


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

    def __init__(self, required_columns: Sequence[str] = ()):
        self.required_columns = tuple(required_columns)

    def format(self, df: pl.DataFrame) -> pl.DataFrame:
        missing_cols = [
            pl.lit(0).cast(pl.Int32).alias(col)
            for col in self.required_columns
            if col not in df.columns
        ]

        if missing_cols:
            df = df.with_columns(missing_cols)

        data_cols = sorted([col for col in df.columns if col != "date"])
        return df.select(["date", *data_cols])


class TimeSeriesPivotBuilder:
    """Transforms raw dictionary data into a padded, clean Polars pivot table."""

    def __init__(self, date_range: YearMonths | MonthDays, columns: Sequence[str] = ()):
        self.date_range = date_range
        self.formatter = DataFrameSchemaFormatter(columns)

    def build(self, raw_data: list[dict], value_column: str) -> pl.DataFrame:
        expected_dates_df = self.date_range.dates()

        if not raw_data:
            return self.formatter.format(expected_dates_df)

        df = pl.DataFrame(raw_data)

        # If the requested value column (like 'exception_sum') doesn't exist
        # return empty schema
        if value_column not in df.columns:
            return self.formatter.format(expected_dates_df)

        pivoted_df = (
            df.group_by(["date", "title"])
            .agg(pl.col(value_column).sum().cast(pl.Int32))
            .pivot(
                index="date",
                on="title",
                values=value_column,
                aggregate_function="first",
            )
        )

        padded_df = expected_dates_df.join(pivoted_df, on="date", how="left").fill_null(
            0
        )

        return self.formatter.format(padded_df)


class MakeDataFrame:
    def __init__(
        self,
        date_range: YearMonths | MonthDays,
        data: list[dict],
        columns: Sequence[str] = (),
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

    @property
    def data(self) -> pl.DataFrame:
        return self._builder.build(self._data, value_column="sum")

    @property
    def exceptions(self) -> pl.DataFrame:
        df = self._builder.build(self._data, value_column="exception_sum")

        if len(df.columns) <= 1:
            return df.with_columns(sum=pl.lit(0).cast(pl.Int32))

        return df.select(
            [pl.col("date"), pl.sum_horizontal(pl.exclude("date")).alias("sum")]
        )
