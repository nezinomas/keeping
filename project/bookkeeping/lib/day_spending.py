from typing import Dict, List

from pandas import DataFrame as DF

from ...core.lib.balance_base import BalanceBase


class DaySpending(BalanceBase):
    _balance = DF()
    _avg_per_day = DF()
    _spending = DF()

    def __init__(self,
                 year: int,
                 month: int,
                 month_df: DF,
                 necessary: List[str],
                 plan_day_sum: float,
                 plan_free_sum: float,
                 exceptions: DF = DF()):

        if not isinstance(month_df, DF):
            return

        if month_df.empty:
            return

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
    def spending(self) -> List[Dict]:
        if self._spending.empty:
            return self._spending

        df = self._spending.copy()
        df.reset_index(inplace=True)

        return df.to_dict('records')

    def _filter(self, df: DF) -> DF:
        col_name_list = [*df.columns]
        col_name_leave = [*set(col_name_list).difference(set(self._necessary))]

        df = df.loc[:, col_name_leave]

        df.drop('total', axis=1, inplace=True)

        return df

    def _get_avg_per_day(self) -> float:
        avg = super().average_month(self._year, self._month)

        return avg.get('total', 0.0)

    def _calc_spending(self, df: DF) -> DF:
        # filter dateframe
        df = self._filter(df)

        # calculate total_row for filtered dataframe
        df.loc[:, 'total'] = df.sum(axis=1)

        # select only total column
        df = df.loc[:, ['total']]

        # remove exceptions sums from total_row
        if not self._exceptions.empty:
            df['total'] = df['total'] - self._exceptions['sum']

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
