import polars as pl
from polars import DataFrame as DF


class BalanceBase:
    def __init__(self, data: DF = DF()):
        self._data = data

    @property
    def balance(self) -> list[dict]:
        """
        Return [{'date': datetime.datetime, 'title': float}]
        """
        return [] if self._data_empty(self._data) else self._data.to_dicts()

    @property
    def types(self) -> list:
        return sorted(self._data.select(pl.exclude("date")).columns)

    @property
    def total(self) -> float:
        """
        Return total sum of all columns
        """
        if self._data_empty(self._data):
            return 0

        return self._data.select(pl.sum(pl.exclude("date")).sum())[0, 0]

    @property
    def total_column(self) -> dict[str, float]:
        if self._data_empty(self._data):
            return []

        df = self._data.select(
            [pl.col("date"), pl.sum(pl.exclude("date")).alias("total")]
        )
        return [] if df.is_empty() else df.to_dicts()

    @property
    def total_row(self) -> dict[str, float]:
        empty = {}
        if self._data_empty(self._data):
            return empty

        df = self._data.select(pl.exclude("date")).sum().head(1)
        return empty if self._data_empty(df) else df.to_dicts()[0]

    @property
    def average(self) -> dict[str, float]:
        """Calculate mean of every column, null values ignored

        Returns:
            dict[str, float]
        """
        empty = {}
        if self._data_empty(self._data):
            return empty

        cols = self._data.select(pl.exclude("date")).columns

        def col_sum(col_name) -> pl.Expr:
            return pl.col(col_name).sum()

        def count_not_nulls(col_name):
            return pl.col(col_name).filter(pl.col(col_name) != 0).count()

        df = (
            self._data.select(cols)
            .fill_null(0)
            .with_columns(
                [
                    pl.when(col_sum(col_name) != 0)
                    .then(col_sum(col_name) / count_not_nulls(col_name))
                    .otherwise(pl.lit(0))
                    for col_name in cols
                ]
            )
        )
        return empty if self._data_empty(df) else df.to_dicts()[0]

    def _data_empty(self, df: DF) -> bool:
        return df.is_empty() if isinstance(df, DF) else True
