from typing import Dict, List

import polars as pl
from polars import DataFrame as DF

from ...core.lib.date import current_day
from .balance_base import BalanceBase
from .make_dataframe import MakeDataFrame


class DaySpending(BalanceBase):
    def __init__(self,
                 df: MakeDataFrame,
                 necessary: List[str],
                 day_input: float,
                 expenses_free: float):

        super().__init__(df.data)

        self._year = df.year
        self._month = df.month
        self._necessary = necessary or []
        self._spending = self._calc_spending(df.data, df.exceptions, day_input, expenses_free)

    @property
    def spending(self) -> List[Dict]:
        if self._spending.is_empty():
            return self._spending

        return self._spending.to_dicts()

    @property
    def avg_per_day(self):
        if self._spending.is_empty():
            return 0.0
        day = current_day(self._year, self._month)
        df = (
            self._spending
            .select(['date', 'total'])
            .with_columns(pl.col('total').filter(pl.col('date').dt.day() <= day).sum() / day)
            .select('total')
        )

        return df[0, 0]

    def _calc_spending(self, df: DF, exceptions: DF, day_input: float, expenses_free: float) -> DF:
        if df.is_empty():
            return df

        def remove_necessary_if_any(df):
            return df.select(pl.exclude(self._necessary)) if self._necessary else df

        df = (
            df
            .pipe(remove_necessary_if_any)
            .with_columns(pl.sum(pl.exclude('date')).alias('total'))
            .select(['date', 'total'])
            .with_columns(pl.Series(name="exceptions", values=exceptions['sum']))
            .with_columns(pl.col('total') - pl.col('exceptions'))
            .drop('exceptions')
            .with_columns((day_input - pl.col('total')).alias('day'))
            .with_columns(
                (expenses_free - (day_input * pl.col('date').dt.day())).alias('teoretical')
            )
            .with_columns((expenses_free - pl.col('total').cumsum()).alias('real'))
            .with_columns((pl.col('real') - pl.col('teoretical')).alias('full'))
        )
        print(f'------------------------------->out \n{df}\n')

        return df
