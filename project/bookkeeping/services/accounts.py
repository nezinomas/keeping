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
        _df = self._make_df(data.incomes, data.expenses)
        _hv = self._make_have(data.have)

        self._table = self._make_table(_df, _hv)

    @property
    def table(self):
        df = self._table.copy().reset_index()

        return df.to_dict('records')

    def _make_df(self, incomes: list[dict], expenses: list[dict]) -> DF:
        col_idx = [
            'id',
            'year',
        ]
        col_num=[
            'past',
            'incomes',
            'expenses',
            'balance',
            'delta',
        ]
        # create df from incomes and expenses
        df = pd.DataFrame(it.chain(incomes, expenses))
        # print(f'created df\n{df}\ncreated have\n{hv}\n')
        if df.empty:
            return pd.DataFrame(columns=col_idx + col_num).set_index(col_idx)

        # create missing columns
        df[[*set(col_num) - set(df.columns)]] = 0.0
        # convert decimal to float
        df[col_num] = df[col_num].astype(float)
        # groupby id, year and sum
        df = df.groupby(col_idx)[col_num].sum(numeric_only=True)

        return df

    def _make_have(self, have: list[dict]) -> DF:
        hv = pd.DataFrame(have)

        if hv.empty:
            return pd.DataFrame(columns=['id', 'year', 'have', 'latest_check'])

        hv['have'] = hv['have'].astype(float)
        return hv

    def _make_table(self, df: DF, hv: DF) -> DF:
        df = df.copy().reset_index().set_index(['id', 'year'])
        hv = hv.copy().reset_index(drop=True).set_index(['id', 'year'])
        # concat df and have; fillna
        df = pd.concat([df, hv], axis=1).fillna(0.0)
        if df.empty:
            return df
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
