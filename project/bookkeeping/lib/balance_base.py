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
        if not isinstance(self._data, DF):
            return []

        return [] if self._data.is_empty() else self._data.to_dicts()

    @property
    def types(self) -> list:
        return sorted(self._data.select(pl.exclude("date")).columns)

    @property
    def total(self) -> float:
        """
        Return total sum of all columns
        """
        if not isinstance(self._data, DF) or self._data.is_empty():
            return 0.0

        return self._data.select(pl.sum(pl.exclude("date")).sum())[0, 0]

    def make_total_column(self, df=DF()) -> DF:
        """
        calculate total column for balance DataFrame

        return filtered DataFrame with date and total column
        """

        if not isinstance(self._data, DF):
            return DF()

        if self._data.is_empty():
            return DF()

        return self._data.select(
            [pl.col("date"), pl.sum(pl.exclude("date")).alias("total")]
        )

    @property
    def total_column(self) -> dict[str, float]:
        return self.make_total_column().to_dicts()

    @property
    def total_row(self) -> dict[str, float]:
        if not isinstance(self._data, DF):
            return {}

        if self._data.is_empty():
            return {}

        df = self._data.select(pl.exclude("date")).sum().head(1)

        return df.to_dicts()[0]

    @property
    def average(self) -> dict[str, float]:
        """Calculate mean of every column, null values ignored

        Returns:
            dict[str, float]
        """
        if not isinstance(self._data, DF):
            return {}

        if self._data.is_empty():
            return {}

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
        return df.to_dicts()[0]
