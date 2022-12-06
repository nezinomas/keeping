import contextlib
import itertools as it
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
        _have = self._make_df_have(_year, data.have)

        self._table = self._make_table(_year, _df, _have)

    @property
    def table(self):
        df = self._table.copy().reset_index()
        df.drop(['year'], axis=1, inplace=True, errors='ignore')

        return df.to_dict('records')

    @property
    def total(self):
        df = self._table.copy().reset_index(drop=True)
        df.drop(['year', 'title'], axis=1, inplace=True, errors='ignore')

        return df.sum().to_dict()

    def _make_df(self, incomes: list[dict], expenses: list[dict]) -> DF:
        columns=[
            'year',
            'title',
            'past',
            'incomes',
            'expenses',
            'balance',
            'have',
            'delta',
        ]

        # create df from incomes and expenses
        df = pd.DataFrame(it.chain(incomes, expenses))

        if df.empty:
            return pd.DataFrame(columns=columns).set_index(['title', 'year'])

        # create missing columns
        df[[*set(columns) - set(df.columns)]] = 0.0
        # nan -> 0.0
        df.fillna(0.0, inplace=True)
        # convert decimal to float
        df[['incomes', 'expenses']] = df[['incomes', 'expenses']].astype(float)
        # groupby title, year and sum
        df = df.groupby(['title', 'year']).sum(numeric_only=True)

        return df

    def _make_df_have(self, year: int, have: list[dict]) -> DF:
        cols = ['title', 'have']

        if not have:
            return pd.DataFrame(columns=cols).set_index('title')

        df = pd.DataFrame(have)
        # create year column from latest_check
        df['year'] = pd.to_datetime(df['latest_check']).dt.year
        # filter rows with current year
        df = df.loc[df['year'] == year]
        # leave title and have columns
        df = df.loc[:,cols].set_index('title')
        # decimal -> float
        df['have'] = df['have'].astype(float)

        return df

    def _make_table(self, year: int, df: DF, have: DF) -> DF:
        df = df.copy().reset_index().set_index('title')
        # copy have column to main df
        df.have = have.have
        # nan -> 0.0
        df.fillna(0.0, inplace=True)
        # if after copy have column, year is empty fill year values
        df.year = df.year.apply(lambda x: x or year)

        if df.empty:
            return df

        # balance without past
        df.balance = df.incomes - df.expenses
        # temp column for each title group with balance cumulative sum
        df['temp'] = df.groupby("title")['balance'].cumsum()
        # calculate past -> shift down temp column
        df['past'] = df.groupby("title")['temp'].shift(fill_value=0.0)
        # recalculate balance with past and drop temp
        df['balance'] = df['past'] + df['incomes'] - df['expenses']
        df.drop(columns=["temp"], inplace=True)
        # calculate delta between have and balance
        df.delta = df.have - df.balance
        # return current year df
        return df.loc[df['year'] == year]
