import calendar
import itertools
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
        self._data = data

    @property
    def data(self):
        return self.create_data(sum_col_name="sum")

    @property
    def exceptions(self):
        df = self.create_data(sum_col_name="exception_sum")

        if df.shape[1] <= 1:
            return df.with_columns(sum=pl.lit(0))

        return df.select([pl.col("date"), pl.sum_horizontal(pl.exclude("date")).alias("sum")])

    def _modify_data(self):
        if not self._data:
            return self._data

        cols = sorted({a["title"] for a in self._data})

        keys = [x for x in self._data[0].keys() if x not in ["date", "title"]]
        data = self._data

        # insert empty values for one month days
        if self.month:
            days = calendar.monthrange(self.year, self.month)[1] + 1
            for title, i in itertools.product(cols, range(1, days)):
                dt = date(self.year, 1, i)
                self._insert_empty_dicts(data, dt, title, keys)
        else:
            # insert empty values form 12 months
            for title, i in itertools.product(cols, range(1, 13)):
                dt = date(self.year, i, 1)
                self._insert_empty_dicts(data, dt, title, keys)

        return data

    def _insert_empty_dicts(self, data, date, title, keys):
        return data.append({
            "date": date,
            "title": title,
            **{x: 0 for x in keys}
        })

    def create_data(self, sum_col_name: str = "sum") -> DF:
        return (
            pl.DataFrame(self._data)
            .pipe(self._insert_missing_rows)
            .select(["date", "title", sum_col_name])
            .sort(["title", "date"])
            .with_columns(pl.col(sum_col_name).cast(pl.Int32))
            .pivot(
                values=sum_col_name,
                index="date",
                columns="title",
                aggregate_function="first",
            )
            .pipe(self._insert_missing_columns)
            .pipe(self._drop_columns)
            .pipe(self._sort_columns)
            .fill_null(0)
            .sort("date")
        )

    def _insert_missing_rows(self, df) -> pl.Expr:
        df_empty = self._empty_df()

        if df.is_empty():
            return df_empty.with_columns(
                title=pl.lit("__tmp_to_drop__"),
                sum=pl.lit(0),
                exception_sum=pl.lit(0),
            )

        return (
            df_empty.join(df, on="date", how="outer")
            .fill_null(0)
            .select(pl.all().forward_fill())
        )

    def _empty_df(self) -> DF:
        if self.month:
            days = calendar.monthrange(self.year, self.month)[1]
            start = date(self.year, self.month, 1)
            end = date(self.year, self.month, days)
            every = "1d"
        else:
            start = date(self.year, 1, 1)
            end = date(self.year, 12, 31)
            every = "1mo"

        rng = pl.date_range(start, end, every, eager=True)
        return pl.DataFrame({"date": rng})

    def _drop_columns(self, df: DF) -> pl.Expr:
        col_to_drop = [
            "__tmp_to_drop__",
            "null",
        ]
        return df.drop([name for name in col_to_drop if name in df.columns])

    def _insert_missing_columns(self, df: DF) -> pl.Expr:
        """Insert missing columns"""
        if not self._columns:
            return df

        cols_diff = set(self._columns) - set(df.columns)
        cols = [pl.lit(0).alias(col_name) for col_name in cols_diff]
        return df.select([pl.all(), *cols])

    def _sort_columns(self, df: DF) -> pl.Expr:
        cols = [pl.col(x) for x in sorted(df.columns[1:])]
        return df.select([pl.col("date"), *cols])
