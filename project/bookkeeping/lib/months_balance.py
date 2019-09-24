from datetime import date
from typing import Dict, List

import pandas as pd

from ..mixins.calc_balance import CalcBalanceMixin, BalanceStats


class MonthsBalance(BalanceStats, CalcBalanceMixin):
    def __init__(self,
                 year,
                 incomes: List[Dict], expenses: List[Dict],
                 amount_start: float=0.0):
        try:
            amount_start = float(amount_start)
        except:
            amount_start = 0.0

        self._amount_start = amount_start
        self._balance = pd.DataFrame()
        self._year = year

        if not incomes and not expenses:
            return

        if not incomes:
            incomes = [{'date': date(year, 1, 1), 'incomes': 0}]

        if not expenses:
            expenses = [{'date': date(year, 1, 1), 'expenses': 0}]

        self._calc(incomes, expenses)

    @property
    def amount_start(self) -> float:
        return self._amount_start

    @property
    def amount_end(self) -> float:
        val = 0.0
        t = super().totals

        return self._amount_start + t['balance'] if t else 0.0

    @property
    def amount_balance(self) -> float:
        t = super().totals

        return t['balance'] if t else 0.0

    @property
    def avg_incomes(self) -> float:
        avg = super().average

        return avg['incomes'] if avg else 0.0

    @property
    def avg_expenses(self) -> float:
        avg = super().average

        return avg['expenses'] if avg else 0.0

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

    def _calc(self, incomes: List[Dict], expenses: List[Dict]) -> None:
        incomes = super().convert_to_df(self._year, incomes)
        expenses = super().convert_to_df(self._year, expenses)

        df = incomes.join(
            expenses,
            how='left', lsuffix='_left', rsuffix='_right',
        ).reset_index()

        # calculate balance
        df.loc[:, 'balance'] = df.incomes - df.expenses

        #  calculate residual amount of money
        # for january
        df.at[0, 'residual'] = self._amount_start + df.at[0, 'balance']

        # for february:december
        for i in range(1, 12):
            df.at[i, 'residual'] = df.at[i, 'balance'] + df.at[i - 1, 'residual']

        # convert date from Timestamp to datetime.date
        df['date'] = df['date'].dt.date

        self._balance = df
