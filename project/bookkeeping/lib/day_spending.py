from typing import Dict, List

from pandas import DataFrame as DF

from .balance_base import BalanceBase
from ...core.lib.date import current_day
from .balance import MakeDataFrame


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

    def _calc_spending(self, df: DF, exceptions: DF, day_input: float, expenses_free: float) -> DF:
        if df.empty:
            return df

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

        df.day = \
            day_input - df.total

        df.teoretical = \
            expenses_free - \
            (day_input * df.index.to_series().dt.day)

        df.real = \
            expenses_free - df.total.cumsum()

        df.full = \
            df.real - df.teoretical

        return df
