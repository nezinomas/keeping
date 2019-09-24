from typing import Dict, List

import pandas as pd


def df_days_of_month(year: int, month: int) -> pd.DataFrame:
    df = None

    try:
        df = pd.DataFrame({
            'date': pd.date_range(
                start=pd.Timestamp(year, month, 1),
                end=pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0),
                freq='D'
            )
        })
    except:
        return df

    df.loc[:, 'total'] = 0.0
    df.set_index('date', inplace=True)

    return df


def df_months_of_year(year: int) -> pd.DataFrame:
    df = None

    try:
        # create empty DataFrame object with index containing all months
        dt_range = pd.date_range(f'{year}', periods=12, freq='MS')

        df = pd.DataFrame(dt_range, columns=['date'])
    except:
        return df

    df.loc[:, 'total'] = 0.0
    df.set_index('date', inplace=True)

    return df


class BalanceStats():
    def __init__(self):
        self._balance = None

    @property
    def balance(self) -> List[Dict]:
        val = []

        if not isinstance(self._balance, pd.DataFrame):
            return val

        if self._balance.empty:
            return val

        arr = self._balance.copy()
        arr.reset_index(inplace=True)

        return arr.to_dict('records')

    @property
    def totals(self) -> Dict[str, float]:
        val = {}

        if not isinstance(self._balance, pd.DataFrame):
            return val

        if self._balance.empty:
            return val

        arr = self._balance.copy()

        return arr.sum().to_dict()

    @property
    def average(self) -> Dict[str, float]:
        val = {}

        if not isinstance(self._balance, pd.DataFrame):
            return val

        if self._balance.empty:
            return val

        # replace 0.0 to None
        # average will be calculated only for months with non zero values
        arr = self._balance.copy()
        arr.replace(0.0, pd.NaT, inplace=True)

        return arr.mean(skipna=True).to_dict()
