from datetime import datetime
from typing import Dict, List

import numpy as np
from pandas import DataFrame as DF


class BalanceBase():
    def __init__(self, data: DF = DF()):
        self._data = data

    @property
    def balance(self) -> List[Dict]:
        '''
        Return [{'date': datetime.datetime, 'title': float}]
        '''
        if not isinstance(self._data, DF):
            return []

        if self._data.empty:
            return []

        arr = self._data.copy()
        arr.reset_index(inplace=True)

        return arr.to_dict('records')

    @property
    def types(self) -> List:
        return sorted(self._data.columns.tolist())

    @property
    def total(self) -> float:
        '''
        Return total sum of all columns
        '''
        if not isinstance(self._data, DF) or self._data.empty:
            return 0.0

        return self._data.sum().sum()

    def make_total_column(self, df = DF()) -> DF:
        '''
        calculate total column for balance DataFrame

        return filtered DataFrame with date and total column
        '''

        df = self._data if df.empty else df

        if not isinstance(df, DF):
            return DF()

        if df.empty:
            return DF()

        df = df.copy()

        df['total'] = df.sum(axis=1)

        return df.reset_index()[['date', 'total']]

    @property
    def total_column(self) -> Dict[str, float]:
        return self.make_total_column().to_dict('records')

    @property
    def total_row(self) -> Dict[str, float]:
        if not isinstance(self._data, DF):
            return {}

        if self._data.empty:
            return {}

        arr = self._data.copy()

        return arr.sum().to_dict()

    @property
    def average(self) -> Dict[str, float]:
        if not isinstance(self._data, DF):
            return {}

        if self._data.empty:
            return {}

        # replace 0.0 to None
        # average will be calculated only for months with non zero values
        arr = self._data.copy()
        arr.replace(0.0, np.nan, inplace=True)
        # calculate average
        arr = arr.mean(skipna=True, numeric_only=True)
        # replace nan -> 0.0
        return arr.fillna(0.0).to_dict()

    def _calc_avg(self, df: DF,
                  year: int, month: int, day: int) -> DF:

        # sort index, in case if dates not ordered
        df.sort_index(inplace=True)

        to_date = datetime(year, month, day)

        sum_ = df.loc[:to_date, :].sum()

        df.loc['total', :] = sum_ / day

        return df
