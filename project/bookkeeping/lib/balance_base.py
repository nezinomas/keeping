import polars as pl


class BalanceBase:
    def __init__(self, data: pl.DataFrame = pl.DataFrame()):
        self._data = data

    @property
    def balance(self) -> list[dict]:
        """
        Return [{'date': datetime.datetime, 'title': float}]
        """
        return [] if self.is_empty(self._data) else self._data.to_dicts()

    @property
    def types(self) -> list:
        return sorted(self._data.select(pl.exclude("date")).columns)

    @property
    def total(self) -> int:
        """
        Return total sum of all columns
        """

        if self.is_empty(self._data):
            return 0

        if self._data.shape[1] <= 1:
            return 0

        return self._data.select(pl.sum_horizontal(pl.exclude("date")).sum())[0, 0]

    @property
    def total_column(self) -> list:
        if self.is_empty(self._data):
            return []

        df = self.sum_cols(self._data, "total")
        return [] if df.is_empty() else df.to_dicts()

    @property
    def total_row(self) -> dict[str, float]:
        if self.is_empty(self._data):
            return {}

        df = self._data.select(pl.exclude("date")).sum().head(1)

        return {} if self.is_empty(df) else df.to_dicts()[0]

    def average_over(self, months: int) -> dict[str, float]:
        """Each column's sum to the year's `months`-th month, over those months: an
        empty month counts, a later one does not, and a year not begun averages 0."""
        if self.is_empty(self._data):
            return {}

        reached = self._data.filter(pl.col("date").dt.month() <= months)
        means = reached.select(pl.exclude("date").sum() / max(months, 1))

        # a frame of dates alone has no column to average
        return {} if self.is_empty(means) else means.to_dicts()[0]

    def is_empty(self, df: pl.DataFrame) -> bool:
        return df.is_empty() if isinstance(df, pl.DataFrame) else True

    def sum_cols(self, df: pl.DataFrame, sum_col_name: str = "sum") -> pl.DataFrame:
        if df.shape[1] <= 1:
            return df.with_columns(sum_col_name=pl.lit(0))

        return df.select(
            [pl.col("date"), pl.sum_horizontal(pl.exclude("date")).alias(sum_col_name)]
        )
