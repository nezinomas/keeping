from operator import itemgetter
from typing import Dict, List, Tuple

from django.utils.translation import gettext as _
from pandas import DataFrame as DF
from pandas import to_datetime

from ...core.lib.balance_base import (BalanceBase, df_days_of_month,
                                      df_months_of_year)
from ...core.lib.colors import CHART


class ExpenseBase(BalanceBase):
    def __init__(self, df: DF, expenses: List[Dict], **kwargs):
        _expenses = self._make_expenses_df(df, expenses)
        _savings = self._make_savings_df(df, kwargs)

        self._exceptions = self._exception_df(df, expenses)
        self._expenses = self._calc_total_column(_expenses, _savings)

        super().__init__(self._expenses)

    @classmethod
    def days_of_month(cls, year, month, expenses, **kwargs) -> DF:
        return cls(df_days_of_month(year, month), expenses, **kwargs)

    @classmethod
    def months_of_year(cls, year, expenses, **kwargs) -> DF:
        return cls(df_months_of_year(year), expenses, **kwargs)

    @property
    def exceptions(self) -> DF:
        return self._exceptions

    @property
    def expenses(self) -> DF:
        return self._expenses

    def _calc_total_column(self, expenses: DF, savings: DF) -> DF:
        df = expenses.copy()
        df = expenses.join(savings)
        df['total'] = df.sum(axis=1)

        return df

    def _make_expenses_df(self, df: DF, lst: List[Dict]) -> DF:
        df = df.copy()
        if not lst:
            return df

        for row in lst:
            df.at[to_datetime(row['date']), row['title']] = float(row['sum'])

        df.fillna(0.0, inplace=True)

        return df

    def _make_savings_df(self, df: DF, lst: Dict[str, Dict]) -> DF:
        df = df.copy()
        if not lst:
            return df

        for title, arr in lst.items():
            for row in arr:
                _title = row.get('title', title)
                df.at[to_datetime(row['date']), title] = float(row['sum'])

        df.fillna(0.0, inplace=True)

        return df

    def _exception_df(self, df: DF, lst: List[Dict]) -> DF:
        df = df.copy()

        if not lst:
            return df

        for row in lst:
            val = row.get('exception_sum', 0.0)
            df.at[to_datetime(row['date']), row['title']] = float(val)

        df.fillna(0.0, inplace=True)

        # sum all title columns
        df['sum'] = df.sum(axis=1)

        # select oncly index and sum columns
        df = df.loc[:, ['sum']]

        return df


class DayExpense():
    def __init__(self, total_row: Dict, **kwargs):
        self._total_row = total_row

    def chart_expenses(self, expenses_types: List[str]) -> List[Dict]:
        rtn = []

        # make List[Dict] from expenses_types and total_row
        for name in expenses_types:
            value = self._total_row.get(name, 0.0)
            arr = {'name': name.upper(), 'y': value}
            rtn.append(arr)

        # sort List[Dict] by y
        rtn = sorted(rtn, key=itemgetter('y'), reverse=True)

        # add to List[Dict] colors
        for key, arr in enumerate(rtn):
            rtn[key]['color'] = CHART[key]

        return rtn

    def chart_targets(self,
                      expenses_types: List[str],
                      targets: Dict
                      ) -> Tuple[List[str], List[float], List[Dict]]:
        tmp = []

        # make List[Dict] from expenses_types and total_row
        for name in expenses_types:
            value = self._total_row.get(name, 0.0)
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

            rtn_categories.append(category.upper())
            rtn_data_target.append(target)
            rtn_data_fact.append({'y': fact, 'target': target})

        return (rtn_categories, rtn_data_target, rtn_data_fact)
