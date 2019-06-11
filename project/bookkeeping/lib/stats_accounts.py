from datetime import date
from decimal import Decimal

import pandas as pd
from .filter_frame import FilterDf


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
        self._calc_(self._data._incomes_past, '+', 'past')
        self._calc_(self._data.savings_past, '-', 'past')
        self._calc_(self._data.expenses_past, '-', 'past')

        self._calc_(self._data.trans_from_past, '-', 'past')
        self._calc_(self._data.trans_to_past, '+', 'past')

    def _calc_balance_now(self):
        # incomes
        self._calc_(self._data.incomes, '+', 'incomes')
        self._calc_(self._data.trans_to, '+', 'incomes')

        # expenses
        self._calc_(self._data.expenses, '-', 'expenses')
        self._calc_(self._data.savings, '-', 'expenses')
        self._calc_(self._data.trans_from, '-', 'expenses')

        # abs expenses
        self._balance.expenses = self._balance.expenses.abs()

        # balance
        self._balance.balance = (
            self._balance.past
            + self._balance.incomes
            - self._balance.expenses
        )

    def _calc_(self, df, action, target_col):
        df = self._group_and_sum(df)
        df = df[['account', 'price']].set_index('account')

        df_index = df.index.tolist()

        for account_title in df_index:
            _price = df.at[account_title, 'price']
            _target = (account_title, target_col)

            if action == '+':
                self._balance.at[_target] += _price

            if action == '-':
                self._balance.at[_target] -= _price

    def _group_and_sum(self, df):
        return (
            df.groupby(['account'])['price']
            .sum()
            .reset_index()
        )
