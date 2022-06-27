from typing import Dict, List

from pandas import DataFrame as DF
from pandas import to_datetime

from ...core.lib.balance_base import (BalanceBase, df_days_of_month,
                                      df_months_of_year)


class ExpenseBase(BalanceBase):
    def __init__(self, df: DF, expenses: List[Dict], **kwargs):
        self._expenses = self._make_expenses_df(df, expenses)
        self._savings = self._make_savings_df(df, kwargs)

        self._exceptions = self._exception_df(df, expenses)
        self._expenses_with_savings = self._join_df(self._expenses, self._savings)

        super().__init__(self._expenses_with_savings)

    @classmethod
    def days_of_month(cls, year, month, expenses, **kwargs):
        return cls(df_days_of_month(year, month), expenses, **kwargs)

    @classmethod
    def months_of_year(cls, year, expenses, **kwargs):
        return cls(df_months_of_year(year), expenses, **kwargs)

    @property
    def exceptions(self) -> DF:
        return self._exceptions

    @property
    def expenses(self) -> DF:
        return self._expenses

    @property
    def types(self) -> List:
        return self._expenses.columns.tolist()

    def _make_expenses_df(self, df: DF, lst: List[Dict], types: List) -> DF:
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
                df.at[to_datetime(row['date']), _title] = float(row['sum'])

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

        # select only index and sum columns
        df = df.loc[:, ['sum']]

        return df
