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

        self._accounts = data.get('account')

        self._past_accounts_balance = self._accounts.copy().set_index('title')

        self._past_accounts_balance.loc[:, 'past'] = 0.00
        # self._past_accounts_balance.loc[:, 'incomes'] = 0.00
        # self._past_accounts_balance.loc[:, 'expenses'] = 0.00
        # self._past_accounts_balance.loc[:, 'balance'] = 0.00

        self._past_balance()
        # self._now_balance()

    @property
    def past_accounts_balance(self):
        return self._past_accounts_balance.to_dict('index')

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
        self._calc_(self._filter_df(self._incomes, 'lt'), '+', 'amount', 'past')
        self._calc_(self._filter_df(self._savings, 'lt'), '-', 'amount', 'past')
        self._calc_(self._filter_df(self._expenses, 'lt'), '-', 'price', 'past')
        self._calc_transactions(self._filter_df(self._transactions, 'lt'))

    def _now_balance(self):
        self._calc_(self._filter_df(self._incomes, 'qte'), '+', 'amount')
        self._calc_(self._filter_df(self._savings, 'qte'), '-', 'amount')
        self._calc_(self._filter_df(self._expenses, 'qte'), '-', 'price')
        self._calc_transactions(self._filter_df(self._transactions, 'qte'))

    def _calc_(self, df, action, col_to_sum, col_add_sum):
        df = self._group_and_sum(df, ['account'], col_to_sum)
        df = df[['account', col_to_sum]].set_index('account')

        df_index = df.index.tolist()

        for index in df_index:
            if action == '+':
                self._past_accounts_balance.loc[index, col_add_sum] += df.loc[index, col_to_sum]
            if action == '-':
                self._past_accounts_balance.loc[index, col_add_sum] -= df.loc[index, col_to_sum]

    def _calc_transactions(self, df):
        df = self._group_and_sum(
            df,
            ['from_account', 'to_account'],
            'amount'
        )

        for index, row in df.iterrows():
            self._past_accounts_balance.loc[row['from_account'], 'past'] -= row['amount']
            self._past_accounts_balance.loc[row['to_account'], 'past'] += row['amount']

    def _group_and_sum(self, df, index, col_to_sum):
        return (
            df.groupby(index)[col_to_sum]
            .sum()
            .reset_index()
        )
