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

        # if there are no accounts
        if data.get('account') is None or data['account'].empty:
            return

        self._balance = data['account']
        self._data = FilterDf(year, data)

        self._prepare_balance()
        self._calc_balance()
        self._calc_worth()

    @property
    def balance(self):
        return (
            self._balance.to_dict('index') if not self._balance.empty
            else self._balance
        )

    @property
    def past_amount(self):
        return self._balance.past.sum() if not self._balance.empty else None

    @property
    def current_amount(self):
        return self._balance.balance.sum() if not self._balance.empty else None

    def _prepare_balance(self):
        self._balance.set_index(['title'], inplace=True)

        # if not self._balance.empty:
        self._balance.loc[:, 'past'] = 0.00
        self._balance.loc[:, 'incomes'] = 0.00
        self._balance.loc[:, 'expenses'] = 0.00
        self._balance.loc[:, 'balance'] = 0.00
        self._balance.loc[:, 'have'] = 0.00
        self._balance.loc[:, 'delta'] = 0.00

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

        cb.calc(self._data.savings_close_to_past, '+', 'past')

    def _calc_balance_now(self):
        cb = CalcBalance('account', self._balance)
        # incomes
        cb.calc(self._data.incomes, '+', 'incomes')
        cb.calc(self._data.trans_to, '+', 'incomes')

        # expenses
        cb.calc(self._data.expenses, '-', 'expenses')
        cb.calc(self._data.savings, '-', 'expenses')
        cb.calc(self._data.trans_from, '-', 'expenses')

        cb.calc(self._data.savings_close_to, '+', 'incomes')

        # abs expenses
        self._balance.expenses = self._balance.expenses.abs()

        # balance
        self._balance.balance = (
            self._balance.past
            + self._balance.incomes
            - self._balance.expenses
        )

    def _calc_worth(self):
        _df = self._data.accounts_worth

        if not isinstance(_df, pd.DataFrame):
            return

        if _df.empty:
            return

        _df.set_index('account', inplace=True)

        _idx = _df.index.tolist()

        # copy market values from savings_worth to _balance
        for i in _idx:
            self._balance.at[i, 'have'] = _df.at[i, 'price']

        self._balance['delta'] = self._balance['have'] - \
            self._balance['balance']
