from typing import List, Dict

import pandas as pd

from ..mixins.calc_balance import BalanceStats
from ...core.lib.utils import get_value_from_dict


class DaySpending(BalanceStats):
    def __init__(self, year: int, month: int, month_df: pd.DataFrame,
                 necessary: List[str], plan_day_sum: float,
                 plan_free_sum: float, exceptions: Dict = {}):

        self._year = year
        self._month = month
        self._necessary = necessary if necessary else []

        self._plan_day_sum = float(plan_day_sum) if plan_day_sum else 0.0
        self._plan_free_sum = float(plan_free_sum) if plan_free_sum else 0.0
        self._exceptions = exceptions

        self._balance = self._calc_spending(month_df)
        self._avg_per_day = self._get_avg_per_day()

        self._spending = self._balance

    @property
    def avg_per_day(self):
        return self._avg_per_day

    @property
    def spending(self):
        df = self._spending.copy()

        if not isinstance(df, pd.DataFrame):
            return df

        if df.empty:
            return df

        df.reset_index(inplace=True)

        return df.to_dict('records')

    def _filter(self, df: pd.DataFrame) -> pd.DataFrame:
        col_name_list = [*df.columns]
        col_name_leave = [*set(col_name_list).difference(set(self._necessary))]

        df = df.loc[:, col_name_leave]

        df.drop('total', axis=1, inplace=True)

        return df

    def _get_avg_per_day(self) -> float:
        avg = super().average_month(self._year, self._month)

        return avg.get('total', 0.0)

    def _calc_spending(self, df: pd.DataFrame) -> pd.DataFrame:
        # filter dateframe
        df = self._filter(df)

        # calculate totals for filtered dataframe
        df.loc[:, 'total'] = df.sum(axis=1)

        # select only total column
        df = df.loc[:, ['total']]

        # remove exceptions sums from totals
        if self._exceptions:
            for ex in self._exceptions:
                cell = (ex['date'], 'total')
                df.loc[cell] = df.loc[cell] - float(ex['sum'])

        df.loc[:, 'teoretical'] = 0.0
        df.loc[:, 'real'] = 0.0
        df.loc[:, 'day'] = 0.0
        df.loc[:, 'full'] = 0.0

        df.day = (
            self._plan_day_sum
            - df.total)

        df.teoretical = (
            self._plan_free_sum
            - (self._plan_day_sum * df.index.to_series().dt.day))

        df.real = (
            self._plan_free_sum
            - df.total.cumsum())

        df.full = (
            df.real
            - df.teoretical)

        return df
