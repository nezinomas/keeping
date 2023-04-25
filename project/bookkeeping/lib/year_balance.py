from datetime import datetime

import polars as pl
from polars import DataFrame as DF

from ..lib.make_dataframe import MakeDataFrame
from .balance_base import BalanceBase


class YearBalance(BalanceBase):
    def __init__(self, data: MakeDataFrame, amount_start: int = 0):
        """
        data: MakeDataFrame object

        amount_start: year start worth amount

        awailable keys in data: incomes, expenses, savings, savings_close, borrow, borrow_return, lend, lend_return
        """
        self._year = data.year
        self._amount_start = amount_start or 0
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
    def avg_incomes(self) -> float:
        return super().average.get("incomes", 0)

    @property
    def avg_expenses(self) -> float:
        _year = datetime.now().year
        _month = datetime.now().month

        # if  now().year == user.profile.year
        # calculate average till current month
        if self._year == _year:
            # self._data is from base class
            df = self._data.select(
                pl.col("expenses").filter(pl.col("date").dt.month() <= _month).sum()
            )
            return df[0, 0] / _month

        return super().average.get("expenses", 0)

    @property
    def income_data(self) -> list[float]:
        return self._balance["incomes"].to_list()

    @property
    def expense_data(self) -> list[float]:
        return self._balance["expenses"].to_list()

    @property
    def borrow_data(self) -> list[float]:
        return self._balance["borrow"].to_list()

    @property
    def borrow_return_data(self) -> list[float]:
        return self._balance["borrow_return"].to_list()

    @property
    def lend_data(self) -> list[float]:
        return self._balance["lend"].to_list()

    @property
    def lend_return_data(self) -> list[float]:
        return self._balance["lend_return"].to_list()

    @property
    def money_flow(self) -> list[float]:
        return self._balance["money_flow"].to_list()

    def _calc_balance_and_money_flow(self, df: DF) -> DF:
        if self.is_empty(df):
            return df

        def add_amount_start_to_money_flow_first_cell(df):
            df[0, "money_flow"] = df[0, "money_flow"] + self.amount_start
            return df

        df = (
            df
            .lazy()
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
                    - pl.col("borrow_return")
                    - pl.col("lend")
                )
            )
            .collect()
            .pipe(add_amount_start_to_money_flow_first_cell)
            .lazy()
            .with_columns(pl.col("money_flow").cumsum())
        )
        return df.collect()
