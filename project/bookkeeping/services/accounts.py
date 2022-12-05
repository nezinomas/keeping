from dataclasses import dataclass, field

import pandas as pd

from ...accounts.models import AccountBalance
from ...core.lib import utils
from ..models import AccountWorth
from . import common


@dataclass
class AccountServiceData:
    year: int

    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        balance_data = AccountBalance.objects.year(self.year)
        worth_data = AccountWorth.objects.items(self.year)

        self.data = common.add_latest_check_key(worth_data, balance_data)


class AccountService:
    def __init__(self, data: AccountServiceData):
        self.data = data.data

    @property
    def total_row(self) -> dict:
        total_row = {
            'past': 0,
            'incomes': 0,
            'expenses': 0,
            'balance': 0,
            'have': 0,
            'delta': 0,
        }

        return \
            utils.sum_all(self.data) if self.data else total_row

class AccountsServiceNew:
    _df = pd.DataFrame()
    _df_have = pd.DataFrame()

    def __init__(self, year, incomes, expenses, have: list[dict] = None):
        self._year = year
        self._have = have
        self._df = self._make_df(incomes, expenses)
        self._df_have = self._make_df_have(have)

    def _make_df(self, incomes, expenses):
        exp = pd.DataFrame(expenses).set_index(['id', 'year']).sort_index(level=['id', 'year'])
        exp['expenses'] = exp['expenses'].astype(float)

        inc = pd.DataFrame(incomes).set_index(['id', 'year']).sort_index(level=['id', 'year'])
        inc['incomes'] = inc['incomes'].astype(float)

        return inc.add(exp, fill_value=0.0).fillna(0.0)

    def _make_df_have(self, have):
        cols = ['title', 'have']

        if not have:
            return pd.DataFrame(columns=cols)

        df = pd.DataFrame(have)
        df = df.loc[:,cols].set_index('title')
        df['have'] = df['have'].astype(float)

        return df

    def table(self):
        df = self._df.copy().reset_index()

        # sum past incomes and expenses
        past = df.loc[df['year'] < self._year].groupby(['id']).sum()
        # filter current year DataFrame
        now = df.loc[
            df['year'] == self._year,
            ['id', 'incomes', 'expenses']].set_index('id')

        # calculate past and current year balances
        now['past'] = past['incomes'] - past['expenses']
        now['balance'] = now['past'] + now['incomes'] - now['expenses']

        # add have
        now['have'] = self._df_have['have']
        now['have'] = now['have'].fillna(0.0)

        # calculate delta between have and balance
        now['delta'] = now['have'] - now['balance']

        return now.reset_index().to_dict('records')
