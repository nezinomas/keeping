import calendar
from datetime import date
from functools import cached_property

import polars as pl


class DateRangeProvider:
    @staticmethod
    def get_dates(year: int, month: int | None = None) -> pl.DataFrame:
        if month:
            days = calendar.monthrange(year, month)[1]
            dates = [date(year, month, d) for d in range(1, days + 1)]
        else:
            dates = [date(year, m, 1) for m in range(1, 13)]

        return pl.DataFrame({"date": dates}).with_columns(pl.col("date").cast(pl.Date))


class DataFrameSchemaFormatter:
    """Handles enforcing required columns and sorting them alphabetically."""

    def __init__(self, required_columns: list[str] | None = None):
        self.required_columns = required_columns or []

    def format(self, df: pl.DataFrame) -> pl.DataFrame:
        # 1. Add any missing columns as 0
        missing_cols = [
            pl.lit(0).cast(pl.Int32).alias(col)
            for col in self.required_columns
            if col not in df.columns
        ]

        if missing_cols:
            df = df.with_columns(missing_cols)

        # 2. Sort columns alphabetically, keeping 'date' first
        data_cols = sorted([col for col in df.columns if col != "date"])
        return df.select(["date", *data_cols])


class TimeSeriesPivotBuilder:
    """Transforms raw dictionary data into a padded, clean Polars pivot table."""

    def __init__(
        self, year: int, month: int | None = None, columns: list[str] | None = None
    ):
        self.year = year
        self.month = month
        self.date_provider = DateRangeProvider()
        self.formatter = DataFrameSchemaFormatter(columns)

    def build(self, raw_data: list[dict], value_column: str) -> pl.DataFrame:
        expected_dates_df = self.date_provider.get_dates(self.year, self.month)

        if not raw_data:
            return self.formatter.format(expected_dates_df)

        df = pl.DataFrame(raw_data)

        # If the requested value column (like 'exception_sum') doesn't exist, return empty schema
        if value_column not in df.columns:
            return self.formatter.format(expected_dates_df)

        # Aggregate and Pivot directly
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

        # "Pad" the missing dates via a LEFT JOIN
        padded_df = expected_dates_df.join(pivoted_df, on="date", how="left").fill_null(
            0
        )

        return self.formatter.format(padded_df)


class MakeDataFrame:
    def __init__(
        self,
        year: int,
        data: list[dict],
        columns: list[str] | None = None,
        month: int | None = None,
    ):
        self.year = year
        self.month = month
        self._columns = columns
        self._data = data

        self._builder = TimeSeriesPivotBuilder(year, month, columns)

    def _debug_print_caller(self, property_name: str):
        import inspect
        """Temporary helper to trace the caller."""
        stack = inspect.stack()
        
        # Loop through the stack to find the first file that ISN'T this one 
        # or a Python/Django internal property wrapper.
        for frame_info in stack:
            filename = frame_info.filename
            if "make_dataframe.py" not in filename and "functools.py" not in filename and "functional.py" not in filename:
                print(f"👉 [MakeDataFrame.{property_name}] called by '{frame_info.function}' in {filename} (Line {frame_info.lineno})")
                break

    @property
    def data(self) -> pl.DataFrame:
        self._debug_print_caller("data")
        r = self._builder.build(self._data, value_column="sum")
        print(f'--------------------------->\n{r}\n')
        return r

    @property
    def exceptions(self) -> pl.DataFrame:
        self._debug_print_caller("exceptions")
        df = self._builder.build(self._data, value_column="exception_sum")

        if len(df.columns) <= 1:
            return df.with_columns(sum=pl.lit(0).cast(pl.Int32))

        r = df.select(
            [pl.col("date"), pl.sum_horizontal(pl.exclude("date")).alias("sum")]
        )
        print(f'--------------------------->\n{r=}\n')
        return r
