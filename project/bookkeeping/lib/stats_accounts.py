from datetime import date
from decimal import Decimal

import pandas as pd

from .filter_frame import FilterDf
from .stats_utils import CalcBalance


class StatsAccounts(object):
    def __init__(self, year, data, *args, **kwargs):
        self._year = year
        self._data = FilterDf(year, data)

        self._balance = pd.DataFrame()
        self._balance_past = None

        if self._data.accounts.empty:
            return

        self._prepare_balance()
        self._calc_balance()

    @property
    def balance(self):
        return (
            self._balance.to_dict('index') if not self._balance.empty
            else self._balance
        )

    @property
    def past_amount(self):
        return self._balance.past.sum() if not self._balance.empty else None

    def _prepare_balance(self):
        self._balance = self._data.accounts.copy()

        self._balance.set_index('title', inplace=True)

        self._balance.loc[:, 'past'] = 0.00
        self._balance.loc[:, 'incomes'] = 0.00
        self._balance.loc[:, 'expenses'] = 0.00
        self._balance.loc[:, 'balance'] = 0.00

    def _calc_balance(self):
        self._calc_balance_past()
        self._calc_balance_now()

    def _calc_balance_past(self):
        blnc = CalcBalance('account', self._balance)
        blnc.calc(self._data.incomes_past, '+', 'past')
        blnc.calc(self._data.savings_past, '-', 'past')
        blnc.calc(self._data.expenses_past, '-', 'past')

        blnc.calc(self._data.trans_from_past, '-', 'past')
        blnc.calc(self._data.trans_to_past, '+', 'past')

    def _calc_balance_now(self):
        blnc = CalcBalance('account', self._balance)
        # incomes
        blnc.calc(self._data.incomes, '+', 'incomes')
        blnc.calc(self._data.trans_to, '+', 'incomes')

        # expenses
        blnc.calc(self._data.expenses, '-', 'expenses')
        blnc.calc(self._data.savings, '-', 'expenses')
        blnc.calc(self._data.trans_from, '-', 'expenses')

        # abs expenses
        self._balance.expenses = self._balance.expenses.abs()

        # balance
        self._balance.balance = (
            self._balance.past
            + self._balance.incomes
            - self._balance.expenses
        )
