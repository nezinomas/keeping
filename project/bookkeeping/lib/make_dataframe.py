import calendar
import itertools
from datetime import date

import polars as pl


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
        self._data = data

    @property
    def data(self):
        return self.create_data(sum_col_name="sum")

    @property
    def exceptions(self):
        df = self.create_data(sum_col_name="exception_sum")

        if df.shape[1] <= 1:
            return df.with_columns(sum=pl.lit(0))

        return df.select(
            [pl.col("date"), pl.sum_horizontal(pl.exclude("date")).alias("sum")]
        )

    def _modify_data(self):
        data = self._data or []

        if data:
            keys = [x for x in self._data[0].keys() if x not in ["date", "title"]]
            cols = sorted({a["title"] for a in self._data})
        else:
            keys = ["sum", "exception_sum"]
            cols = ["__tmp_to_drop__"]

        # insert empty values for one month days
        if self.month:
            days = calendar.monthrange(self.year, self.month)[1] + 1
            for title, i in itertools.product(cols, range(1, days)):
                dt = date(self.year, self.month, i)
                data.append(self._insert_empty_dicts(dt, title, keys))
        # insert empty values for 12 months
        else:
            for title, i in itertools.product(cols, range(1, 13)):
                dt = date(self.year, i, 1)
                data.append(self._insert_empty_dicts(dt, title, keys))

        return data

    def _insert_empty_dicts(self, dt, title, keys):
        return {"date": dt, "title": title, **{x: 0 for x in keys}}

    def create_data(self, sum_col_name: str = "sum") -> pl.DataFrame:
        data = self._modify_data()

        return (
            pl.DataFrame(data)
            .pipe(self._group_and_sum)
            .sort([pl.col.title, pl.col.date])
            .select(["date", "title", sum_col_name])
            .sort(["title", "date"])
            .with_columns(pl.col(sum_col_name).cast(pl.Int32))
            .pivot(
                values=sum_col_name,
                index="date",
                on="title",
                aggregate_function="first",
            )
            .pipe(self._insert_missing_columns)
            .pipe(self._drop_columns)
            .pipe(self._sort_columns)
            .fill_null(0)
            .sort("date")
        )

    def _group_and_sum(self, df):
        cols = df.columns
        return df.group_by([pl.col.date, pl.col.title]).agg(
            [pl.col(i).sum() for i in cols if i not in ["date", "title"]]
        )

    def _drop_columns(self, df: pl.DataFrame) -> pl.Expr:
        col_to_drop = [
            "__tmp_to_drop__",
        ]
        return df.drop([name for name in col_to_drop if name in df.columns])

    def _insert_missing_columns(self, df: pl.DataFrame) -> pl.Expr:
        """Insert missing columns"""
        if not self._columns:
            return df

        cols_diff = set(self._columns) - set(df.columns)
        cols = [pl.lit(0).alias(col_name) for col_name in cols_diff]

        return df.select([pl.all(), *cols])

    def _sort_columns(self, df: pl.DataFrame) -> pl.Expr:
        cols = [pl.col(x) for x in sorted(df.columns[1:])]
        return df.select([pl.col("date"), *cols])
