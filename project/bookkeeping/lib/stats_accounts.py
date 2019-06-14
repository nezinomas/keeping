from datetime import date
from decimal import Decimal

import pandas as pd

from .filter_frame import FilterDf
from .stats_utils import CalcBalance


class StatsAccounts(object):
    def __init__(self, year, data, *args, **kwargs):
        self._year = year
        self._balance = pd.DataFrame()
        self._balance_past = None

        self._data = FilterDf(year, data)
        if not isinstance(self._data.expenses, pd.DataFrame) or self._data.expenses.empty:
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
        try:
            self._balance = (
                pd.DataFrame(
                    self._data.expenses.account.unique(),
                    columns=['title'],
                ).
                set_index(['title'])
            )
        except:
            pass

        # if not self._balance.empty:
        self._balance.loc[:, 'past'] = 0.00
        self._balance.loc[:, 'incomes'] = 0.00
        self._balance.loc[:, 'expenses'] = 0.00
        self._balance.loc[:, 'balance'] = 0.00

    def _calc_balance(self):
        self._calc_balance_past()
        self._calc_balance_now()

    def _calc_balance_past(self):
        cb = CalcBalance('account', self._balance)

        cb.calc(self._data.incomes_past, '+', 'past')
        cb.calc(self._data.savings_past, '-', 'past')
        cb.calc(self._data.expenses_past, '-', 'past')

        cb.calc(self._data.trans_from_past, '-', 'past')
        cb.calc(self._data.trans_to_past, '+', 'past')

    def _calc_balance_now(self):
        cb = CalcBalance('account', self._balance)
        # incomes
        cb.calc(self._data.incomes, '+', 'incomes')
        cb.calc(self._data.trans_to, '+', 'incomes')

        # expenses
        cb.calc(self._data.expenses, '-', 'expenses')
        cb.calc(self._data.savings, '-', 'expenses')
        cb.calc(self._data.trans_from, '-', 'expenses')

        # abs expenses
        self._balance.expenses = self._balance.expenses.abs()

        # balance
        self._balance.balance = (
            self._balance.past
            + self._balance.incomes
            - self._balance.expenses
        )
