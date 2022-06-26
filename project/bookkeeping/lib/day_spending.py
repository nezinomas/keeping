from typing import Dict, List

from pandas import DataFrame as DF
from project.bookkeeping.lib.expense_summary import ExpenseBase

from ...core.lib.date import current_day


class DaySpending(ExpenseBase):
    _balance = DF()

    def __init__(self,
                 year: int,
                 month: int,
                 expenses: List[Dict],
                 necessary: List[str],
                 plan_day_sum: float,
                 plan_free_sum: float,
                 ):

        self.E = ExpenseBase.days_of_month(year, month, expenses)

        self._year = year
        self._month = month
        self._necessary = necessary if necessary else []

        self._plan_day_sum = float(plan_day_sum) if plan_day_sum else 0.0
        self._plan_free_sum = float(plan_free_sum) if plan_free_sum else 0.0
        self._exceptions = self.E.exceptions

        self._balance = self._calc_spending(self.E.expenses)

    @property
    def spending(self) -> List[Dict]:
        if self._balance.empty:
            return self._balance

        df = self._balance.copy()
        df.reset_index(inplace=True)

        return df.to_dict('records')

    @property
    def avg_per_day(self):
        return self._get_avg_per_day().get('total', 0.0)

    def _filter(self, df: DF) -> DF:
        col_name_list = [*df.columns]
        col_name_leave = [*set(col_name_list).difference(set(self._necessary))]

        df = df.loc[:, col_name_leave]

        return df

    def _get_avg_per_day(self) -> float:
        if not isinstance(self._balance, DF):
            return {}

        if self._balance.empty:
            return {}

        day = current_day(self._year, self._month)

        df = self._balance.copy()
        df = self._calc_avg(df, self._year, self._month, day)

        # select onvly last row for returning
        row = df.loc['total', :]

        return row.to_dict()

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
