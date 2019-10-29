from datetime import datetime
from operator import itemgetter
from typing import Dict, List

from pandas import DataFrame as DF

from ...core.lib.colors import CHART
from ...core.mixins.calc_balance import (BalanceStats, df_days_of_month,
                                         df_months_of_year)


class Expenses():
    def __init__(self, df: DF, expenses: List[Dict], **kwargs):
        _expenses = self._expenses_df(df, expenses)
        _savings = self._savings_df(df, kwargs)

        self._exceptions = self._exception_df(df, expenses)
        self._expenses = self._calc(_expenses, _savings)

    @property
    def exceptions(self) -> List[Dict]:
        val = []

        if self._exceptions.empty:
            return val

        arr = self._exceptions.copy()
        arr.reset_index(inplace=True)

        return arr.to_dict('records')

    @property
    def expenses(self) -> DF:
        return self._expenses

    def _calc(self, expenses: DF, savings: DF) -> DF:
        df = expenses.copy()
        df = expenses.join(savings)
        df['total'] = df.sum(axis=1)

        return df

    def _expenses_df(self, df: DF, lst: List[Dict]) -> DF:
        df = df.copy()
        if not lst:
            return df

        for row in lst:
            df.at[row['date'], row['title']] = float(row['sum'])

        df.fillna(0.0, inplace=True)

        return df

    def _savings_df(self, df: DF, lst: Dict[str, Dict]) -> DF:
        df = df.copy()
        if not lst:
            return df

        for title, arr in lst.items():
            for row in arr:
                _title = row.get('title', title)
                df.at[row['date'], title] = float(row['sum'])

        df.fillna(0.0, inplace=True)

        return df

    def _exception_df(self, df: DF, lst: List[Dict]) -> DF:
        df = df.copy()

        if not lst:
            return df

        for row in lst:
            val = row.get('exception_sum', 0.0)
            df.at[row['date'], 'exception'] = float(val)

        df.fillna(0.0, inplace=True)

        return df


class MonthExpenseType(BalanceStats, Expenses):
    def __init__(self, year: int, month: int, expenses: List[Dict], **kwargs):
        self._balance = df_days_of_month(year, month)

        Expenses.__init__(self, self._balance, expenses, **kwargs)

        self._balance = self.expenses

    @property
    def total(self):
        t = super().total_row

        return t.get('total', 0.0)

    def chart_expenses(self, expenses_types: List[str]) -> List[Dict]:
        total_row = super().total_row
        rtn = []

        # make List[Dict] from expenses_types and total_row
        for name in expenses_types:
            value = total_row.get(name, 0.0)
            arr = {'name': name.upper(), 'y': value}
            rtn.append(arr)

        # sort List[Dict] by y
        rtn = sorted(rtn, key=itemgetter('y'), reverse=True)

        # and to List[Dict] colors
        for key, arr in enumerate(rtn):
            rtn[key]['color'] = CHART[key]

        return rtn

    def chart_targets(self, expenses_types: List[str],
                      targets: Dict) -> (List[str], List[float], List[Dict]):
        total_row = super().total_row
        tmp = []

        # make List[Dict] from expenses_types and total_row
        for name in expenses_types:
            value = total_row.get(name, 0.0)
            arr = {'name': name, 'y': value}
            tmp.append(arr)

        # sort List[Dict] by y
        tmp = sorted(tmp, key=itemgetter('y'), reverse=True)

        rtn_categories = []
        rtn_data_fact = []
        rtn_data_target = []

        for arr in tmp:
            category = arr['name']
            target = float(targets.get(category, 0.0))
            fact = float(arr['y'])

            color = 'green'

            if fact > target and target > 0:
                color = 'red'

            rtn_categories.append(category.upper())
            rtn_data_target.append(target)
            rtn_data_fact.append({'y': fact, 'color': color})

        return (rtn_categories, rtn_data_target, rtn_data_fact)


class MonthsExpenseType(BalanceStats, Expenses):
    def __init__(self, year, expenses: List[Dict], **kwargs):
        self._balance = df_months_of_year(year)

        Expenses.__init__(self, self._balance, expenses, **kwargs)

        self._balance = self.expenses

    @property
    def chart_data(self) -> List[Dict[str, float]]:
        rtn = []
        arr = super().total_row

        if arr:
            # delete total cell
            del arr['total']

            # sort dictionary
            arr = dict(sorted(arr.items(), key=lambda x: x[1], reverse=True))

            # transfort arr for pie chart
            rtn = [{'name': key, 'y': value} for key, value in arr.items()]
        return rtn

    @property
    def total_column(self) -> Dict[str, float]:
        val = {}

        if not isinstance(self._balance, DF):
            return val

        if self._balance.empty:
            return val

        df = self._balance.copy()
        df = df.reset_index()
        df = df.rename(columns={'total': 'sum'})
        df = df[['date', 'sum']]

        return df.to_dict('records')
