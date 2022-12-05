from dataclasses import dataclass, field

import pandas as pd
from pandas import DataFrame as DF

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


@dataclass
class AccountServiceDataNew:
    year: int
    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    have: list[dict] = field(init=False, default_factory=list)


class AccountsServiceNew:
    _df = pd.DataFrame()
    _have = pd.DataFrame()

    def __init__(self, data: AccountServiceDataNew):
        _year = data.year
        _df = self._make_df(data.incomes, data.expenses)
        _have = self._make_df_have(data.have)

        self._table = self._make_table(_year, _df, _have)


    @property
    def table(self):
        return self._table.copy().reset_index().to_dict('recods')

    @property
    def total(self):
        return self._table.copy().sum().to_dict()

    def _make_df(self, incomes: list[dict], expenses: list[dict]) -> DF:
        columns=[
            'year',
            'title',
            'incomes',
            'expenses',
            'balance',
            'have',
            'delta',
        ]
        df = pd.DataFrame(columns=columns).set_index(['title', 'year'])

        def to_df(arr):
            df = pd.DataFrame(arr)
            df.set_index(['title', 'year'], inplace=True)
            df.sort_index(level=['title', 'year'])
            # convert column [incomes or expenses] decimal values to float
            df[df.columns] = df[df.columns].astype(float)
            return df

        if expenses:
            df = df.add(to_df(expenses), fill_value=0.0)

        if incomes:
            df = df.add(to_df(incomes), fill_value=0.0)

        df.fillna(0.0, inplace=True)

        return df

    def _make_df_have(self, have: list[dict]) -> DF:
        cols = ['title', 'have']

        if not have:
            return pd.DataFrame(columns=cols)

        df = pd.DataFrame(have)
        df = df.loc[:,cols].set_index('title')
        df['have'] = df['have'].astype(float)

        return df

    def _make_table(self, year: int, df: DF, have: DF) -> DF:
        df = df.copy().reset_index()
        # sum past incomes and expenses
        past = df.loc[df['year'] < year].groupby(['title']).sum()
        # get current year DataFrame
        now = df.loc[df['year'] == year].set_index('title')
        # add have columns form self._have DataFrame
        now.have = have.have

        if past.empty and now.empty:
            return df

        # calculate past balance
        now.loc[:, 'past'] = 0.0 if past.empty else past.incomes - past.expenses
        # nan -> 0.0
        now.fillna(0.0, inplace=True)
        # calculate current year balance
        now.balance = now.past + now.incomes - now.expenses
        # calculate delta between have and balance
        now.delta = now.have - now.balance
        # delete year column
        del now['year']

        return now
