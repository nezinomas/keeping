from operator import itemgetter
from datetime import datetime
from typing import Dict, List

import pandas as pd

from ...core.lib.colors import CHART
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

    @property
    def total(self):
        t = super().totals

        return t.get('total', 0.0)

    def chart_expenses(self, expenses_types: List[str]) -> List[Dict]:
        totals = super().totals
        rtn = []

        # make List[Dict] from expenses_types and totals
        for name in expenses_types:
            value = totals.get(name, 0.0)
            arr = {'name': name.upper(), 'y': value}
            rtn.append(arr)

        # sort List[Dict] by y
        rtn = sorted(rtn, key=itemgetter('y'), reverse=True)

        # and to List[Dict] colors
        for key, arr in enumerate(rtn):
            rtn[key]['color'] = CHART[key]

        return rtn


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
