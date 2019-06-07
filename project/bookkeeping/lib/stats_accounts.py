import pandas as pd
from django_pandas.io import read_frame

from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving, SavingType
from ...transactions.models import Transaction
from ..lib.accounts import Accounts


def _print(*args):
    for a in args:
        print('\n\n>>>\n')
        print(a)
        print('\n<<<\n')


class StatsAccounts(object):
    def __init__(self, year):
        self._year = year

        self._accounts = Accounts().accounts_dictionary

        self._past_balance()

    @property
    def past_accounts_balance(self):
        return self._past_accounts_balance

    def _past_balance(self):
        accounts = {**self._accounts}

        qs = Income.objects.past_items(**{'year': self._year})
        self._calc_(accounts, qs, '+')

        qs = Saving.objects.past_items(**{'year': self._year})
        self._calc_(accounts, qs, '-')

        qs = Expense.objects.past_items(**{'year': self._year})
        self._calc_(accounts, qs, '-', 'price')

        qs = Transaction.objects.past_items(**{'year': self._year})
        self._calc_transactions(accounts, qs)

        self._past_accounts_balance = accounts

    def _calc_(self, accounts, qs, action, amount_col_name='amount'):
        df = self._read_frame(qs, ['account'], amount_col_name)
        df = df[['account', amount_col_name]].set_index('account')

        df_index = df.index.tolist()

        for index in df_index:
            if action == '+':
                accounts[index] += df.loc[index, amount_col_name]
            if action == '-':
                accounts[index] -= df.loc[index, amount_col_name]

    def _calc_transactions(self, accounts, qs):
        df = self._read_frame(
            qs,
            ['from_account', 'to_account'],
            'amount'
        )

        for index, row in df.iterrows():
            accounts[row['from_account']] -= row['amount']
            accounts[row['to_account']] += row['amount']

    def _read_frame(self, qs, index, col_to_sum):
        df = read_frame(qs)
        df = df.groupby(index)[col_to_sum].sum().reset_index()

        return df
