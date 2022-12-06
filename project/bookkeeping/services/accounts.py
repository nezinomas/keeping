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
    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    have: list[dict] = field(init=False, default_factory=list)


class AccountsServiceNew:
    _df = pd.DataFrame()
    _have = pd.DataFrame()

    def __init__(self, data: AccountServiceDataNew):
        _df = self._make_df(data.incomes, data.expenses, data.have)

        self._table = self._make_table(_df)

    @property
    def table(self):
        df = self._table.copy().reset_index()

        return df.to_dict('records')

    def _make_df(self, incomes: list[dict], expenses: list[dict], have: list[dict]) -> DF:
        index = [
            'id',
            'year',
        ]
        columns=[
            'past',
            'incomes',
            'expenses',
            'balance',
            'have',
            'delta',
        ]

        # create df from incomes and expenses
        df = pd.DataFrame(it.chain(incomes, expenses, have))

        if df.empty:
            return pd.DataFrame(columns=index + columns).set_index(index)

        # create missing columns
        df[[*set(columns) - set(df.columns)]] = 0.0
        # nan -> 0.0
        df.fillna(0.0, inplace=True)
        # convert decimal to float
        df[columns] = df[columns].astype(float)
        # groupby id, year and sum
        df = df.groupby(index)[columns].sum(numeric_only=True)

        return df

    def _make_table(self, df: DF) -> DF:
        df = df.copy().reset_index().set_index('id')
        if df.empty: return df
        # balance without past
        df.balance = df.incomes - df.expenses
        # temp column for each id group with balance cumulative sum
        df['temp'] = df.groupby("id")['balance'].cumsum()
        # calculate past -> shift down temp column
        df['past'] = df.groupby("id")['temp'].shift(fill_value=0.0)
        # recalculate balance with past and drop temp
        df['balance'] = df['past'] + df['incomes'] - df['expenses']
        df.drop(columns=["temp"], inplace=True)
        # calculate delta between have and balance
        df.delta = df.have - df.balance

        return df
