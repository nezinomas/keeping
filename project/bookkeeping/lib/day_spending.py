import calendar
from typing import List

import pandas as pd

from ..mixins.calc_balance import BalanceStats


class DaySpending(BalanceStats):
    def __init__(self, month: int, month_df: pd.DataFrame,
                 necessary: List[str], plan_day_sum: float, plan_free_sum: List[str]):

        self._month = month
        self._necessary = necessary

        self._plan_day_sum = self._get_value_form_list(plan_day_sum)
        self._plan_free_sum = self._get_value_form_list(plan_free_sum)

        self._balance = self._filter(month_df)
        self._avg_per_day = self._get_avg_per_day()

        self._spending = self._calc_spending(self._balance)

    @property
    def plan_per_day(self):
        return self._plan_day_sum

    @property
    def avg_per_day(self):
        return self._avg_per_day

    @property
    def plan_free_sum(self):
        return self._plan_free_sum

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

        df = df[col_name_leave]
        df['total'] = df.sum(axis=1)

        return df

    def _month_name(self):
        return calendar.month_name[self._month].lower()

    def _get_value_form_list(self, arr: List[str]) -> float:
        return arr.get(self._month_name(), 0.0)

    def _get_avg_per_day(self) -> float:
        avg = super().average

        return avg.get('total', 0.0)

    def _calc_spending(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[['total']]

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
