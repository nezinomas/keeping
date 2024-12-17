import polars as pl

from ...core.lib.date import current_day
from .balance_base import BalanceBase
from .make_dataframe import MakeDataFrame


class DaySpending(BalanceBase):
    def __init__(
        self,
        expense: MakeDataFrame,
        necessary: list[str],
        free: float,
        per_day: float,
    ):
        super().__init__(expense.data)

        self._year = expense.year
        self._month = expense.month
        self._per_day = per_day
        self._free = free
        self._necessary = necessary or []
        self._spending = self._calculate_spending(expense.data, expense.exceptions)

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

    def _calculate_spending(
        self, df: pl.DataFrame, exceptions: pl.DataFrame
    ) -> pl.DataFrame:
        if df.is_empty():
            return df

        if df.shape[1] <= 1:
            df = df.with_columns(total=pl.lit(0))

        return (
            df.pipe(self._remove_necessary_if_any)
            .lazy()
            .with_columns(total=pl.sum_horizontal(pl.exclude("date")))
            .select(["date", "total"])
            .with_columns(pl.Series(name="exceptions", values=exceptions["sum"]))
            .with_columns(total=(pl.col("total") - pl.col("exceptions")))
            .drop("exceptions")
            .pipe(self._calculate_spending_columns)
            .collect()
        )

    def _remove_necessary_if_any(self, df: pl.DataFrame) -> pl.Expr:
        return df.select(pl.exclude(self._necessary)) if self._necessary else df

    def _calculate_spending_columns(self, df: pl.DataFrame) -> pl.Expr:
        return (
            df.with_columns(day=(self._per_day - pl.col("total")))
            .with_columns(
                teoretical=(self._free - (self._per_day * pl.col("date").dt.day()))
            )
            .with_columns(real=(self._free - pl.col("total").cum_sum()))
            .with_columns(full=(pl.col("real") - pl.col("teoretical")))
        )
