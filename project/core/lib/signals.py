import contextlib
import itertools as it
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from pandas import DataFrame as DF


@dataclass
class GetData:
    conf: dict[tuple] = field(default_factory=dict)
    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    have: list[dict] = field(init=False, default_factory=list)
    types: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = self._get_data(self.conf.get('incomes'), 'incomes')
        self.expenses = self._get_data(self.conf.get('expenses'), 'expenses')
        self.have = self._get_data(self.conf.get('have'), 'have')
        self.types = self._get_data(self.conf.get('types'), 'related')

    def _get_data(self, models: tuple, method: str):
        items = []

        if not models:
            return items

        for model in models:
            with contextlib.suppress(AttributeError):
                _method = getattr(model.objects, method)
                if _qs := _method():
                    items.extend(_qs)
        return items


class SignalBase(ABC):
    @property
    def types(self) -> dict:
        return {category.id: category for category in self._types}

    @property
    def table(self):
        df = self._table.copy().reset_index()
        return df.to_dict('records')

    @abstractmethod
    def make_table(self, df: DF) -> DF:
        ...

    def _make_df(self, arr: list[dict], cols: list) -> DF:
        col_idx = ['id', 'year']
        # create df from incomes and expenses
        df = pd.DataFrame(arr)
        if df.empty:
            return pd.DataFrame(columns=col_idx + cols).set_index(col_idx)
        # create missing columns
        df[[*set(cols) - set(df.columns)]] = 0.0
        # convert decimal to float
        df[cols] = df[cols].astype(np.float64)
        # groupby id, year and sum
        df = df.groupby(col_idx)[cols].sum(numeric_only=True)

        return df

    def _make_have(self, have: list[dict]) -> DF:
        hv = pd.DataFrame(have)
        idx = ['id', 'year']
        if hv.empty:
            cols = ['id', 'year', 'have', 'latest_check']
            return pd.DataFrame(defaultdict(list), columns=cols).set_index(idx)
        # convert Decimal -> float
        hv['have'] = hv['have'].apply(pd.to_numeric, downcast='float')

        return hv.set_index(idx)

    def _insert_missing_values(self, df: DF, field_name: str) -> DF:
        df = self._insert_missing_types(df)
        df = self._insert_missing_latest(df, field_name)
        df = self._insert_future_data(df)
        return df

    def _insert_future_data(self, df: DF) -> DF:
        ''' copy last year values into future (year + 1) '''
        # last year in dataframe
        year = df.index.levels[1].max()
        # get last group of (year, id)
        last_group = df.groupby(['year', 'id']).last().loc[year]
        return self._reset_values(year + 1, df, last_group)

    def _insert_missing_types(self, df: DF) -> DF:
        '''
            copy types: (account | saving_type | pension_type)
            from previous year to current year
        '''
        index = list(df.index)
        index_id = list(df.index.levels[0])
        index_year = list(df.index.levels[1])
        # years index should have at least two years
        if index_year and len(index_year) < 2:
            return df
        last_year = index_year[-1]
        prev_year = index_year[-2]
        arr = []
        for _type in self._types:
            # if type id not id dataframe index
            if (_type.pk) not in index_id:
                continue
            # if type dont have record in previous year
            if (_type.pk, prev_year) not in index:
                continue
            # if type have record in current year
            if (_type.pk, last_year) in index:
                continue
            arr.append(_type.pk)
        # get rows to be copied from previous year
        values_id = df.index.get_level_values(0)
        values_year = df.index.get_level_values(1)
        mask = (values_id.isin(arr)) & (values_year==prev_year)

        return self._reset_values(last_year, df, df[mask])

    def _insert_missing_latest(self, df: DF, field_name: str) -> DF:
        '''
            copy latest_check and (have | market_value) if they are empty
            from previous year to current year
        '''
        index = list(df.index)
        index_id = list(df.index.levels[0])
        index_year = list(df.index.levels[1])
        # years index should have at least two years
        if len(index_year) < 2:
            return df
        last_year = index_year[-1]
        prev_year = index_year[-2]
        for pk in index_id:
            if (pk, prev_year) not in index:
                continue
            # get field value
            have = df.at[(pk, last_year), field_name]
            if have:
                continue
            # copy field and latest_check values from previous year
            df.at[(pk, last_year), 'latest_check'] = df.at[(pk, prev_year), 'latest_check']
            df.at[(pk, last_year), field_name] = df.at[(pk, prev_year), field_name]
        return df

    def _reset_values(self, year: int, df: DF, df_filtered: DF) -> DF:
        df_filtered = df_filtered.reset_index().copy()
        df_filtered['year'] = year
        df_filtered.set_index(['id', 'year'], inplace=True)
        if 'fee' in df.columns:
            df_filtered[['incomes', 'fee', 'sold', 'sold_fee']] = 0.0
        else:
            df_filtered[['incomes', 'expenses']] = 0.0
        df = pd.concat([df, df_filtered])
        return df.sort_index()


class Accounts(SignalBase):
    def __init__(self, data: GetData):
        cols = ['incomes', 'expenses']
        _df = self._make_df(it.chain(data.incomes, data.expenses), cols)
        _hv = self._make_have(data.have)
        _df = self._join_df(_df, _hv)

        self._types = data.types
        self._table = self.make_table(_df)

    def make_table(self, df: DF) -> DF:
        if df.empty:
            return df
        df = self._insert_missing_values(df, 'have')
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

    def _join_df(self, df: DF, hv: DF) -> DF:
        df = pd.concat([df, hv], axis=1).fillna(0.0)
        df[['past', 'balance', 'delta']] = 0.0
        return df


class Savings(SignalBase):
    def __init__(self, data: GetData):
        cols = ['incomes', 'expenses', 'fee']
        _in = self._make_df(data.incomes, cols)
        _ex = self._make_df(data.expenses, cols)
        _hv = self._make_have(data.have)
        _df = self._join_df(_in, _ex, _hv)

        self._types = data.types
        self._table = self.make_table(_df)

    def make_table(self, df: DF) -> DF:
        if df.empty:
            return df
        df = self._insert_missing_values(df, 'market_value')
        # calculate incomes
        df.per_year_incomes = df.incomes
        df.per_year_fee = df.fee
        # past_amount and past_fee
        df = self._calc_past(df)
        # calculate sold
        df.sold = df.groupby("id")['sold'].cumsum()
        df.sold_fee = df.groupby("id")['sold_fee'].cumsum()
        # recalculate incomes and fees with past values
        df.incomes = df.past_amount + df.per_year_incomes
        df.fee = df.past_fee + df.per_year_fee
        # calculate invested, invested cannot by negative
        df.invested = df.incomes - df.fee - df.sold - df.sold_fee
        df.invested = df.invested.mask(df.invested < 0, 0.0)
        # calculate profit/loss
        df.profit_sum = df.market_value - df.invested
        df.profit_proc = \
            df[['market_value', 'invested']].apply(Savings.calc_percent, axis=1)
        return df

    def _calc_past(self, df: DF) -> DF:
        df['tmp'] = df.groupby("id")['per_year_incomes'].cumsum()
        df.past_amount = df.groupby("id")['tmp'].shift(fill_value=0.0)
        # calculate past_fee
        df['tmp'] = df.groupby("id")['per_year_fee'].cumsum()
        df.past_fee = df.groupby("id")['tmp'].shift(fill_value=0.0)
        # drop tmp columns
        df.drop(columns=['tmp'], inplace=True)
        return df

    def _join_df(self, inc: DF, exp: DF, hv: DF) -> DF:
        # drop expenses column
        inc.drop(columns=['expenses'], inplace=True)
        # drop incomes column, rename fee
        exp.drop(columns=['incomes'], inplace=True)
        exp.rename(columns={'fee': 'sold_fee', 'expenses': 'sold'}, inplace=True)
        # concat dataframes, sum fees
        df = pd.concat([inc, exp, hv], axis=1).fillna(0.0)
        # rename have -> market_value
        df.rename(columns={'have': 'market_value'}, inplace=True)
        # create columns
        cols = [
            'past_amount', 'past_fee',
            'per_year_incomes', 'per_year_fee',
            'invested',
            'profit_proc', 'profit_sum']
        df[cols] = 0.0

        return df

    @staticmethod
    def calc_percent(args):
        market = args[0]
        invested = args[1]

        rtn = 0.0
        if invested:
            rtn = ((market * 100) / invested) - 100

        return rtn
