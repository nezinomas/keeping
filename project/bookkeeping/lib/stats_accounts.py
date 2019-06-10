from datetime import date

import pandas as pd
from django_pandas.io import read_frame


class FilterDf(object):
    def __init__(self, year, data):
        self._year = year

        _incomes = data.get('income')
        _expenses = data.get('expense')
        _savings = data.get('saving')
        _trans = data.get('transaction')

        self._incomes = self._filter_df(_incomes, 'gte')
        self._incomes_past = self._filter_df(_incomes, 'lt')

        self._expenses = self._filter_df(_expenses, 'gte')
        self._expenses_past = self._filter_df(_expenses, 'lt')

        self._savings = self._filter_df(_savings, 'gte')
        self._savings_past = self._filter_df(_savings, 'lt')

        self._trans_from = self._filter_trans(_trans, 'from_account', 'gte')
        self._trans_from_past = self._filter_trans(_trans, 'from_account', 'lt')

        self._trans_to = self._filter_trans(_trans, 'to_account', 'gte')
        self._trans_to_past = self._filter_trans(_trans, 'to_account', 'lt')

        self._accounts = data.get('account').set_index('title')

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
        start = pd.to_datetime(date(self._year, 1, 1))
        if action == 'lt':
            df = df[df['date'] < start]

        if action == 'gte':
            df = df[df['date'] >= start]

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

        self._prepare_balance()
        self._calc_balance()

    @property
    def balance(self):
        return self._balance.to_dict('index')

    def _prepare_balance(self):
        self._balance = self._data.accounts.copy()

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
            if action == '+':
                self._balance.loc[account_title, target_col] += df.loc[account_title, 'price']

            if action == '-':
                self._balance.loc[account_title, target_col] -= df.loc[account_title, 'price']

    def _group_and_sum(self, df):
        return (
            df.groupby(['account'])['price']
            .sum()
            .reset_index()
        )
