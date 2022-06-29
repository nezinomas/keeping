from typing import Dict, List

from pandas import DataFrame as DF
from pandas import to_datetime

from ...core.lib.balance_base import (BalanceBase, df_days_of_month,
                                      df_months_of_year)


class ExpenseBalance(BalanceBase):
    def __init__(self, df: DF, expenses: List[Dict], types: List[str]):
        self._expenses = self._make_expenses_df(df, expenses, types)
        self._exceptions = self._exception_df(df, expenses)

        super().__init__(self._expenses)

    @classmethod
    def days_of_month(cls, year, month, expenses, types, **kwargs):
        return cls(df_days_of_month(year, month), expenses, types, **kwargs)

    @classmethod
    def months_of_year(cls, year, expenses, types, **kwargs):
        return cls(df_months_of_year(year), expenses, types, **kwargs)

    @property
    def exceptions(self) -> DF:
        return self._exceptions

    @property
    def expenses(self) -> DF:
        return self._expenses

    @property
    def types(self) -> List:
        return sorted(self._expenses.columns.tolist())

    def _make_expenses_df(self, df: DF, lst: List[Dict], types: List) -> DF:
        df = df.copy()

        # create column for each type
        df[types] = 0.0

        if not lst:
            return df

        for row in lst:
            title = row.get('title', 'sum')
            df.at[to_datetime(row['date']), title] = float(row['sum'])

        df.fillna(0.0, inplace=True)

        return df

    def _exception_df(self, df: DF, lst: List[Dict]) -> DF:
        df = df.copy()

        if not lst:
            return df

        for row in lst:
            title = row.get('title', 'sum')
            val = row.get('exception_sum', 0.0)

            df.at[to_datetime(row['date']), title] = float(val)

        df.fillna(0.0, inplace=True)

        # sum all title columns
        df['sum'] = df.sum(axis=1)

        # select only index and sum columns
        df = df.loc[:, ['sum']]

        return df
