from datetime import date
from decimal import Decimal

import pandas as pd
from django_pandas.io import read_frame
from ...core.tests.utils import _print


class FilterDf(object):
    def __init__(self, year, data):
        self._year = year

        self._accounts = data.get('account')

        _incomes = data.get('income')

        self._incomes = self._filter_df(_incomes, 'eq')
        self._incomes_past = self._filter_df(_incomes, 'lt')

        _expenses = data.get('expense')
        self._expenses = self._filter_df(_expenses, 'eq')
        self._expenses_past = self._filter_df(_expenses, 'lt')

        _savings = data.get('saving')
        self._savings = self._filter_df(_savings, 'eq')
        self._savings_past = self._filter_df(_savings, 'lt')

        _trans = data.get('transaction')
        self._trans_from = self._filter_trans(_trans, 'from_account', 'eq')
        self._trans_from_past = self._filter_trans(_trans, 'from_account', 'lt')

        self._trans_to = self._filter_trans(_trans, 'to_account', 'eq')
        self._trans_to_past = self._filter_trans(_trans, 'to_account', 'lt')

    @property
    def accounts(self):
        return self._accounts

    @property
    def incomes(self):
        return self._incomes

    @property
    def incomes_past(self):
        return self._incomes_past

    @property
    def expenses(self):
        return self._expenses

    @property
    def expenses_past(self):
        return self._expenses_past

    @property
    def savings(self):
        return self._savings

    @property
    def savings_past(self):
        return self._savings_past

    @property
    def trans_from(self):
        return self._trans_from

    @property
    def trans_from_past(self):
        return self._trans_from_past

    @property
    def trans_to(self):
        return self._trans_to

    @property
    def trans_to_past(self):
        return self._trans_to_past

    def _filter_df(self, df, action):
        if action == 'lt':
            df = df[df['date'].dt.year < self._year]

        if action == 'eq':
            df = df[df['date'].dt.year == self._year]

        return df

    def _filter_trans(self, df, column, action):
        _df = self._filter_df(df, action)

        _df = _df.loc[:, [column, 'price']]
        _df.rename({column: 'account'}, axis=1, inplace=True)

        return _df


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
            price = df.at[account_title, 'price']

            if action == '+':
                self._balance.at[account_title, target_col] += price

            if action == '-':
                self._balance.at[account_title, target_col] -= price

    def _group_and_sum(self, df):
        return (
            df.groupby(['account'])['price']
            .sum()
            .reset_index()
        )
