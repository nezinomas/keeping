import calendar
from datetime import date

import polars as pl
from polars import DataFrame as DF


class MakeDataFrame:
    def __init__(
        self, year: int, data: list[dict], columns: list = None, month: int = None
    ):
        """Create polars DataFrame from list of dictionaries

        Parameters
        ---------
        year: int

        data: list[dict]
            [{date, sum, exception_sum, title},]

        columns: list|tuple
            Optional.
            For insertation of additional columns

        month: int
            Optional.
            If value: DataFrame rows will be days of that month
            If no value: DataFrame rows will be 12 months
        """
        self.year = year
        self.month = month
        self._columns = columns
        self._data = self._transform_data(data)

    @property
    def exceptions(self):
        df = self.create_data(sum_col_name="exception_sum")
        if df.is_empty():
            return df

        return df.select([pl.col("date"), pl.sum(pl.exclude("date")).alias("sum")])

    @property
    def data(self):
        return self.create_data(sum_col_name="sum")

    def create_data(self, sum_col_name: str = "sum") -> DF:
        return (
            pl.DataFrame(self._data)
            .select(["date", "title", sum_col_name])
            .sort(["title", "date"])
            .with_columns(pl.col(sum_col_name).cast(pl.Float32))
            .pipe(self._insert_missing_rows)
            .pivot(values=sum_col_name, index="date", columns="title")
            .pipe(self._insert_missing_columns)
            .pipe(self._drop_columns)
            .pipe(self._sort_columns)
            .fill_null(0)
            .sort("date")
        )

    def _drop_columns(self, df: DF) -> pl.Expr:
        col_to_drop = [
            "__tmp_to_drop__",
        ]
        return df.drop([name for name in col_to_drop if name in df.columns])

    def _transform_data(self, data: list[dict]) -> list[dict]:
        """Add first and last dates if data is empty"""
        data = data or []
        data = data if isinstance(data, list) else list(data)

        if self.month:
            first_date = date(self.year, self.month, 1)
            last_date = date(
                self.year, self.month, calendar.monthrange(self.year, self.month)[1]
            )
        else:
            first_date = date(self.year, 1, 1)
            last_date = date(self.year, 12, 31)

        common = {"title": "__tmp_to_drop__", "sum": 0.0, "exception_sum": 0.0}
        data.extend(({"date": first_date, **common}, {"date": last_date, **common}))
        return data

    def _insert_missing_columns(self, df: DF) -> pl.Expr:
        """Insert missing columns"""
        if not self._columns:
            return df

        cols_diff = set(self._columns) - set(df.columns)
        cols = [pl.lit(0).alias(col_name) for col_name in cols_diff]
        return df.select([pl.all(), *cols])

    def _insert_missing_rows(self, df: DF) -> pl.Expr:
        every = "1d" if self.month else "1mo"
        return df.upsample(
            time_column="date", every=every, by="title", maintain_order=True
        ).with_columns(pl.col("title").forward_fill())

    def _sort_columns(self, df: DF) -> pl.Expr:
        cols = [pl.col(x) for x in sorted(df.columns[1:])]
        return df.select([pl.col("date"), *cols])
