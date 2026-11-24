from datetime import date
from functools import cached_property

import polars as pl

from ...core.lib.year_boundary import YearBoundary
from ..lib.make_dataframe import MakeDataFrame
from .balance_base import BalanceBase


class YearBalance(BalanceBase):
    def __init__(self, data: MakeDataFrame, amount_start: int = 0, *, today: date):
        self.year = data.date_range.year
        self._amount_start = amount_start
        self._boundary = YearBoundary(self.year, today)
        self._balance = self._calc_balance_and_money_flow(data.data)

        super().__init__(self._balance)

    @property
    def amount_start(self) -> float:
        return self._amount_start

    @property
    def amount_end(self) -> float:
        try:
            val = self._balance["money_flow"][-1]
        except pl.exceptions.ColumnNotFoundError:
            val = 0

        return val

    @property
    def amount_balance(self) -> float:
        return super().total_row.get("balance", 0)

    @property
    def is_coming(self) -> bool:
        return self._boundary.is_coming

    @cached_property
    def average(self) -> dict[str, float]:
        """Over the months the year has reached: all twelve once it is over."""
        return self.average_over(self._boundary.months_elapsed)

    @property
    def avg_incomes(self) -> float:
        return self.average.get("incomes", 0)

    @property
    def avg_expenses(self) -> float:
        return self.average.get("expenses", 0)

    @property
    def money_flow(self) -> list[float]:
        return self._balance["money_flow"].to_list()

    def _calc_balance_and_money_flow(self, df: pl.DataFrame) -> pl.DataFrame:
        if df.is_empty():
            return df

        account_fee = pl.lit(0)
        if "savings_account_fee" in df.columns:
            account_fee = pl.col("savings_account_fee")

        def add_amount_start_to_money_flow_first_cell(df):
            df[0, "money_flow"] = df[0, "money_flow"] + self.amount_start
            return df

        df = (
            df.lazy()
            .sort("date")
            .with_columns(balance=(pl.col("incomes") - pl.col("expenses")))
            .with_columns(
                money_flow=(
                    pl.lit(0)
                    + pl.col("balance")
                    + pl.col("savings_close")
                    + pl.col("borrow")
                    + pl.col("lend_return")
                    - pl.col("savings")
                    - account_fee
                    - pl.col("borrow_return")
                    - pl.col("lend")
                )
            )
            .collect()
            .pipe(add_amount_start_to_money_flow_first_cell)
            .lazy()
            .with_columns(pl.col("money_flow").cum_sum())
        )
        return df.collect()
