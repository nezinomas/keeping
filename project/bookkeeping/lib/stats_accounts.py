from datetime import date

import pandas as pd
from django_pandas.io import read_frame


def _print(*args):
    for a in args:
        print('\n\n>>>\n')
        print(a)
        print('\n<<<\n')


class StatsAccounts(object):
    def __init__(self, year, data, *args, **kwargs):
        self._year = year

        self._incomes = data.get('income')
        self._expenses = data.get('expense')
        self._savings = data.get('saving')
        self._transactions = data.get('transaction')
        self._accounts = self._accounts_dict(data.get('account'))

        self._past_balance()

    @property
    def past_accounts_balance(self):
        return self._past_accounts_balance

    def _filter_df(self, df, action):
        start = pd.to_datetime(date(self._year, 1, 1))
        if action == 'lt':
            df = df[df['date'] < start]

        if action == 'gte':
            df = df[df['date'] >= start]

        return df

    def _accounts_dict(self, df):
        _df = df.to_dict(orient='list')
        return {title: 0 for title in _df['title']}

    def _past_balance(self):
        accounts = {**self._accounts}

        self._calc_(accounts, self._filter_df(self._incomes, 'lt'), '+')
        self._calc_(accounts, self._filter_df(self._savings, 'lt'), '-')
        self._calc_(accounts, self._filter_df(self._expenses, 'lt'), '-', 'price')
        self._calc_transactions(accounts, self._filter_df(self._transactions, 'lt'))

        self._past_accounts_balance = accounts

    def _calc_(self, accounts, df, action, amount_col_name='amount'):
        df = self._group_and_sum(df, ['account'], amount_col_name)
        df = df[['account', amount_col_name]].set_index('account')

        df_index = df.index.tolist()

        for index in df_index:
            if action == '+':
                accounts[index] += df.loc[index, amount_col_name]
            if action == '-':
                accounts[index] -= df.loc[index, amount_col_name]

    def _calc_transactions(self, accounts, df):
        df = self._group_and_sum(
            df,
            ['from_account', 'to_account'],
            'amount'
        )

        for index, row in df.iterrows():
            accounts[row['from_account']] -= row['amount']
            accounts[row['to_account']] += row['amount']

    def _group_and_sum(self, df, index, col_to_sum):
        return (
            df.groupby(index)[col_to_sum]
            .sum()
            .reset_index()
        )
