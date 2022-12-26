from datetime import datetime
from typing import Dict, List

import numpy as np
from pandas import DataFrame as DF


class BalanceBase():
    def __init__(self, balance: DF = DF()):
        self._balance = balance

    @property
    def balance(self) -> List[Dict]:
        '''
        Return [{'date': datetime.datetime, 'title': float}]
        '''
        if not isinstance(self._balance, DF):
            return []

        if self._balance.empty:
            return []

        arr = self._balance.copy()
        arr.reset_index(inplace=True)

        return arr.to_dict('records')

    @property
    def types(self) -> List:
        return sorted(self._balance.columns.tolist())

    @property
    def total(self) -> float:
        '''
        Return total sum of all columns
        '''
        if not isinstance(self._balance, DF) or self._balance.empty:
            return 0.0

        return self._balance.sum().sum()

    def make_total_column(self, df = DF()) -> DF:
        '''
        calculate total column for balance DataFrame

        return filtered DataFrame with date and total column
        '''

        df = self._balance if df.empty else df

        if not isinstance(df, DF):
            return DF()

        if df.empty:
            return DF()

        df = df.copy()

        df['total'] = df.sum(axis=1)

        df = df.reset_index()
        df = df[['date', 'total']]

        return df

    @property
    def total_column(self) -> Dict[str, float]:
        return self.make_total_column().to_dict('records')

    @property
    def total_row(self) -> Dict[str, float]:
        if not isinstance(self._balance, DF):
            return {}

        if self._balance.empty:
            return {}

        arr = self._balance.copy()

        return arr.sum().to_dict()

    @property
    def average(self) -> Dict[str, float]:
        if not isinstance(self._balance, DF):
            return {}

        if self._balance.empty:
            return {}

        # replace 0.0 to None
        # average will be calculated only for months with non zero values
        arr = self._balance.copy()
        arr.replace(0.0, np.nan, inplace=True)

        # calculate average
        arr = arr.mean(skipna=True, numeric_only=True)

        # replace nan -> 0.0
        arr = arr.fillna(0.0)

        return arr.to_dict()

    def _calc_avg(self, df: DF,
                  year: int, month: int, day: int) -> DF:

        # sort index, in case if dates not ordered
        df.sort_index(inplace=True)

        to_date = datetime(year, month, day)

        sum_ = df.loc[:to_date, :].sum()

        df.loc['total', :] = sum_ / day

        return df
