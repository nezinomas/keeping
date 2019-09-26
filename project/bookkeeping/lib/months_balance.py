from datetime import date
from typing import Dict, List

import pandas as pd

from ..mixins.calc_balance import (BalanceStats, df_days_of_month,
                                   df_months_of_year)


class MonthsBalance(BalanceStats):
    def __init__(self, year: int, incomes: List[Dict],
                 expenses: List[Dict], savings: List[Dict]=[],
                 savings_close: List[Dict]=[], amount_start: float=0.0):

        '''
        year: int

        incomes: [{'date': datetime.date(), 'incomes': Decimal()}, ... ]

        expenses: [{'date': datetime.date(), 'expenses': Decimal()}, ... ]

        savings: [{'date': datetime.date(), 'savings': Decimal()}, ... ]

        savings_close: [{'date': datetime.date(), 'to_account': Decimal()}, ... ]

        amount_start: year start worth amount
        '''

        super().__init__()

        try:
            amount_start = float(amount_start)
        except:
            amount_start = 0.0

        self._amount_start = amount_start

        if not incomes and not expenses:
            return

        self._balance = self._make_df(year, incomes, expenses, savings, savings_close)
        self._balance = self._calc(self._balance)

    @property
    def amount_start(self) -> float:
        return self._amount_start

    @property
    def amount_end(self) -> float:
        val = 0.0
        t = super().totals

        return self._amount_start + t.get('balance', 0.0)

    @property
    def amount_balance(self) -> float:
        t = super().totals

        return t.get('balance', 0.0)

    @property
    def avg_incomes(self) -> float:
        avg = super().average

        return avg.get('incomes', 0.0)

    @property
    def avg_expenses(self) -> float:
        avg = super().average

        return avg.get('expenses', 0.0)

    @property
    def income_data(self) -> List[float]:
        rtn = []
        if 'incomes' in self._balance:
            rtn = self._balance.incomes.tolist()

        return rtn

    @property
    def expense_data(self) -> List[float]:
        rtn = []
        if 'expenses' in self._balance:
            rtn = self._balance.expenses.tolist()

        return rtn

    @property
    def save_data(self) -> List[float]:
        rtn = []
        if 'residual' in self._balance:
            rtn = self._balance.residual.tolist()

        return rtn

    def _make_df(self, year: int, incomes: List[Dict], expenses: List[Dict],
                 savings: List[Dict], savings_close: List[Dict]) -> pd.DataFrame:

        df = df_months_of_year(year)

        # append necessary columns
        df.loc[:, 'incomes'] = 0.0
        df.loc[:, 'expenses'] = 0.0
        df.loc[:, 'residual'] = 0.0
        df.loc[:, 'balance'] = 0.0
        df.loc[:, 'savings'] = 0.0
        df.loc[:, 'savings_close'] = 0.0

        # copy incomes values, convert Decimal to float
        for d in incomes:
            df.at[d['date'], 'incomes'] = float(d['incomes'])

        # copy expenses values, convert Decimal to float
        for d in expenses:
            df.at[d['date'], 'expenses'] = float(d['expenses'])

        if savings:
            # copy savings values, convert Decimal to float
            for d in savings:
                df.at[d['date'], 'savings'] = float(d['savings'])

        if savings_close:
            # copy savings values, convert Decimal to float
            for d in savings_close:
                df.at[d['date'], 'savings_close'] = float(d['to_account'])

        return df

    def _clean_df(self, df: pd.DataFrame) -> pd.DataFrame:
        # delete not necessary columns
        df.drop('savings', axis=1, inplace=True)
        df.drop('savings_close', axis=1, inplace=True)
        df.drop('total', axis=1, inplace=True)

        return df

    def _calc(self, df: pd.DataFrame) -> pd.DataFrame:
        # calculate balance
        df['incomes'] = df.incomes + df.savings_close
        df['expenses'] = df.expenses + df.savings
        df['balance'] = df.incomes - df.expenses

        #  calculate residual amount of money
        # for january
        df.loc[df.index[0], 'residual'] = (
            0.0
            + self._amount_start
            + df.loc[df.index[0], 'balance']
        )

        # for february:december
        for i in range(1, 12):
            idx = df.index[i]
            idx_prev = df.index[i - 1]

            df.loc[idx, 'residual'] = (
                0.0
                + df.loc[idx, 'balance']
                + df.loc[idx_prev, 'residual']
            )

        df = self._clean_df(df)

        return df
