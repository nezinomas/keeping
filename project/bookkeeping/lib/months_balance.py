from datetime import date

import pandas as pd

from ..mixins.calc_balance import CalcBalanceMixin


class MonthsBalance(CalcBalanceMixin):
    def __init__(self, year, incomes, expenses, amount_start=0.0):
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
    def balance(self):
        val = None
        balance = self._balance.copy()

        if not balance.empty:
            val = balance.to_dict('records')

        return val

    @property
    def amount_start(self):
        return self._amount_start

    @property
    def amount_end(self):
        val = 0.0

        if self.totals:
            val = self._amount_start + self.totals['balance']

        return val

    @property
    def amount_balance(self):
        val = 0.0

        if self.totals:
            val = self.totals['balance']

        return val

    @property
    def avg_incomes(self):
        val = 0.0

        if self.average:
            val = self.average['incomes']

        return val

    @property
    def avg_expenses(self):
        val = 0.0

        if self.average:
            val = self.average['expenses']

        return val

    @property
    def totals(self):
        return super().totals(self._balance)

    @property
    def average(self):
        return super().average(self._balance)

    @property
    def income_data(self):
        rtn = []
        if 'incomes' in self._balance:
            rtn = self._balance.incomes.tolist()

        return rtn

    @property
    def expense_data(self):
        rtn = []
        if 'expenses' in self._balance:
            rtn = self._balance.expenses.tolist()

        return rtn

    @property
    def save_data(self):
        rtn = []
        if 'residual' in self._balance:
            rtn = self._balance.residual.tolist()

        return rtn

    def _calc(self, incomes, expenses):
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
