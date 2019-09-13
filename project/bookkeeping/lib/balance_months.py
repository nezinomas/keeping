import pandas as pd

from ..mixins.calc_balance import CalcBalanceMixin


class BalanceMonths(CalcBalanceMixin):
    def __init__(self, incomes, expenses, amount_start=0.0):
        try:
            amount_start = float(amount_start)
        except:
            amount_start = 0.0

        self._amount_start = amount_start
        self._balance = pd.DataFrame()

        if not incomes and not expenses:
            return

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
    def balance_amount(self):
        val = 0.0

        if self.totals:
            val = self.totals['balance']

        return val

    @property
    def totals(self):
        return super().totals(self._balance)

    @property
    def average(self):
        return super().average(self._balance)

    def _calc(self, incomes, expenses):
        incomes = super().convert_to_df(incomes)
        expenses = super().convert_to_df(expenses)

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
