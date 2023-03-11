import polars as pl
from polars import DataFrame as DF

from ...core.lib.date import current_day
from .balance_base import BalanceBase
from .make_dataframe import MakeDataFrame


class DaySpending(BalanceBase):
    def __init__(
        self,
        df: MakeDataFrame,
        necessary: list[str],
        day_input: float,
        expenses_free: float,
    ):
        super().__init__(df.data)

        self._year = df.year
        self._month = df.month
        self._day_input = day_input
        self._expenses_free = expenses_free
        self._necessary = necessary or []
        self._spending = self._make_df(df.data, df.exceptions)

    @property
    def spending(self) -> list[dict]:
        if self._spending.is_empty():
            return self._spending

        return self._spending.to_dicts()

    @property
    def avg_per_day(self) -> float:
        if self._spending.is_empty():
            return 0
        day = current_day(self._year, self._month)
        df = (
            self._spending.select(["date", "total"])
            .with_columns(
                pl.col("total").filter(pl.col("date").dt.day() <= day).sum() / day
            )
            .select("total")
        )
        return df[0, 0]

    def _make_df(self, df: DF, exceptions: DF) -> DF:
        if df.is_empty():
            return df

        df = (
            df.pipe(self._remove_necessary_if_any)
            .with_columns(pl.sum(pl.exclude("date")).alias("total"))
            .select(["date", "total"])
            .with_columns(pl.Series(name="exceptions", values=exceptions["sum"]))
            .with_columns(total=(pl.col("total") - pl.col("exceptions")))
            .drop("exceptions")
            .pipe(self._calc_spending)
        )
        return df

    def _remove_necessary_if_any(self, df: DF) -> pl.Expr:
        return df.select(pl.exclude(self._necessary)) if self._necessary else df

    def _calc_spending(self, df: DF) -> pl.Expr:
        return (
            df.with_columns(day=self._day_input - pl.col("total"))
            .with_columns(
                teoretical=(
                    self._expenses_free - (self._day_input * pl.col("date").dt.day())
                )
            )
            .with_columns(real=self._expenses_free - pl.col("total").cumsum())
            .with_columns(full=pl.col("real") - pl.col("teoretical"))
        )
