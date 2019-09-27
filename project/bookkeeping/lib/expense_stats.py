from datetime import datetime
from typing import Dict, List

import pandas as pd

from ..mixins.calc_balance import (BalanceStats, df_days_of_month,
                                   df_months_of_year)


def calc(expenses: List[Dict], df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    # copy values from expenses to data_frame
    for d in expenses:
        df.at[d['date'], d['title']] = float(d['sum'])

    if kwargs:
        for title, arr in kwargs.items():
            for row in arr:
                if 'date' in row and 'sum' in row:
                    df.at[row['date'], title] = float(row['sum'])

    df.fillna(0.0, inplace=True)

    df['total'] = df.sum(axis=1)

    return df


class MonthExpenseType(BalanceStats):
    def __init__(self, year: int, month: int, expenses: List[Dict], **kwargs):
        self._balance = df_days_of_month(year, month)

        if not expenses:
            return

        self._balance = calc(expenses, self._balance, **kwargs)

    @property
    def balance_df(self):
        return self._balance


class MonthsExpenseType(BalanceStats):
    def __init__(self, year, expenses: List[Dict], **kwargs):
        self._balance = df_months_of_year(year)

        if not expenses:
            return

        self._balance = calc(expenses, self._balance, **kwargs)

    @property
    def chart_data(self) -> List[Dict[str, float]]:
        rtn = []
        arr = super().totals

        if arr:
            # delete total cell
            del arr['total']

            # sort dictionary
            arr = dict(sorted(arr.items(), key=lambda x: x[1], reverse=True))

            # transfort arr for pie chart
            rtn = [{'name': key, 'y': value} for key, value in arr.items()]
        return rtn
