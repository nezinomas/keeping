from datetime import datetime
from typing import Dict, List

import pandas as pd
from pandas import DataFrame as DF

from ...core.lib.date import current_day


def df_days_of_month(year: int, month: int) -> DF:
    df = DF()

    try:
        df = DF({
            'date': pd.date_range(
                start=pd.Timestamp(year, month, 1),
                end=pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0),
                freq='D'
            )
        })
    except:
        return df

    df.set_index('date', inplace=True)

    return df


def df_months_of_year(year: int) -> DF:
    df = DF()

    try:
        # create empty DataFrame object with index containing all months
        dt_range = pd.date_range(f'{year}', periods=12, freq='MS')

        df = DF(dt_range, columns=['date'])
    except:
        return df

    df.set_index('date', inplace=True)

    return df


class BalanceBase():
    def __init__(self):
        self._balance = DF()

    @property
    def balance(self) -> List[Dict]:
        val = []

        if not isinstance(self._balance, DF):
            return val

        if self._balance.empty:
            return val

        arr = self._balance.copy()
        arr.reset_index(inplace=True)

        return arr.to_dict('records')

    @property
    def total_row(self) -> Dict[str, float]:
        val = {}

        if not isinstance(self._balance, DF):
            return val

        if self._balance.empty:
            return val

        arr = self._balance.copy()

        return arr.sum().to_dict()

    @property
    def average(self) -> Dict[str, float]:
        val = {}

        if not isinstance(self._balance, DF):
            return val

        if self._balance.empty:
            return val

        # replace 0.0 to None
        # average will be calculated only for months with non zero values
        arr = self._balance.copy()
        arr.replace(0.0, pd.NaT, inplace=True)

        # calculate average
        arr = arr.mean(skipna=True)

        # replace nan -> 0.0
        arr = arr.fillna(0.0)

        return arr.to_dict()

    def average_month(self, year: int, month: int) -> Dict[str, float]:
        val = {}

        if not isinstance(self._balance, DF):
            return val

        if self._balance.empty:
            return val

        day = current_day(year, month)

        df = self._balance.copy()
        df = self._calc_avg(df, year, month, day)

        # select onvly last row for returning
        row = df.loc['total', :]

        return row.to_dict()

    def _calc_avg(self, df: DF,
                  year: int, month: int, day: int) -> DF:

        # sort index, in case if dates not ordered
        df.sort_index(inplace=True)

        to_date = datetime(year, month, day)

        sum_ = df.loc[:to_date, :].sum()

        df.loc['total', :] = sum_ / day

        return df
