from typing import Dict, List

from pandas import DataFrame as DF
from project.bookkeeping.lib.expense_summary import (ExpenseBalance,
                                                     df_days_of_month)

from ...core.lib.date import current_day
from ...core.lib.utils import get_value_from_dict
from ...plans.lib.calc_day_sum import PlanCalculateDaySum


class DaySpending(ExpenseBalance):
    def __init__(self,
                 year: int,
                 month: int,
                 expenses: List[Dict],
                 types: List[str],
                 necessary: List[str],
                 plans: PlanCalculateDaySum):

        super().__init__(df_days_of_month(year, month), expenses, types)

        self._year = year
        self._month = month
        self._necessary = necessary if necessary else []

        self._spending = self._calc_spending(self.expenses, self.exceptions, plans)

    @property
    def spending(self) -> List[Dict]:
        if self._spending.empty:
            return self._spending

        df = self._spending.copy()
        df.reset_index(inplace=True)

        return df.to_dict('records')

    @property
    def avg_per_day(self):
        return self._get_avg_per_day().get('total', 0.0)

    def _delete_columns_marked_as_necessary(self, df: DF) -> DF:
        col_name_list = [*df.columns]
        col_name_leave = [*set(col_name_list).difference(set(self._necessary))]

        df = df.loc[:, col_name_leave]

        return df

    def _get_avg_per_day(self) -> float:
        if not isinstance(self._spending, DF):
            return {}

        if self._spending.empty:
            return {}

        day = current_day(self._year, self._month)

        df = self._spending.copy()
        df = self._calc_avg(df, self._year, self._month, day)

        # select onvly last row for returning
        row = df.loc['total', :]

        return row.to_dict()

    def _calc_spending(self, df: DF, exceptions: DF, plans: PlanCalculateDaySum) -> DF:
        # filter dateframe
        df = self._delete_columns_marked_as_necessary(df)

        # calculate total_row for filtered dataframe
        df.loc[:, 'total'] = df.sum(axis=1)

        # select only total column
        df = df.loc[:, ['total']]

        # remove exceptions sums from total_row
        if not exceptions.empty:
            df['total'] = df['total'] - exceptions['sum']

        df.loc[:, 'teoretical'] = 0.0
        df.loc[:, 'real'] = 0.0
        df.loc[:, 'day'] = 0.0
        df.loc[:, 'full'] = 0.0

        plan_day_sum = get_value_from_dict(plans.day_input, self._month)
        plan_free_sum = get_value_from_dict(plans.expenses_free, self._month)

        df.day = \
            plan_day_sum - df.total

        df.teoretical = \
            plan_free_sum - \
            (plan_day_sum * df.index.to_series().dt.day)

        df.real = \
            plan_free_sum - df.total.cumsum()

        df.full = \
            df.real - df.teoretical

        return df
