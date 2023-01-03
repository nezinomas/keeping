import contextlib
import itertools as it
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from django.db.models import Model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from pandas import DataFrame as DF

from ..accounts import models as account
from ..bookkeeping import models as bookkeeping
from ..debts import models as debt
from ..expenses import models as expense
from ..incomes import models as income
from ..pensions import models as pension
from ..savings import models as saving
from ..transactions import models as transaction


# ----------------------------------------------------------------------------
#                                                               AccountBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=income.Income)
@receiver(post_delete, sender=income.Income)
@receiver(post_save, sender=expense.Expense)
@receiver(post_delete, sender=expense.Expense)
@receiver(post_save, sender=saving.Saving)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_save, sender=transaction.Transaction)
@receiver(post_delete, sender=transaction.Transaction)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_save, sender=debt.Debt)
@receiver(post_delete, sender=debt.Debt)
@receiver(post_save, sender=debt.DebtReturn)
@receiver(post_delete, sender=debt.DebtReturn)
@receiver(post_save, sender=bookkeeping.AccountWorth)
def accounts_signal(sender: object, instance: object, *args, **kwargs):
    data = accounts_data()
    categories = get_categories(account.Account)
    objects = create_objects(account.AccountBalance, categories, data)
    save_objects(account.AccountBalance, objects)


def accounts_data():
    conf = {
        'incomes': (
            income.Income,
            debt.Debt,
            debt.DebtReturn,
            transaction.Transaction,
            transaction.SavingClose,
        ),
        'expenses': (
            expense.Expense,
            debt.Debt,
            debt.DebtReturn,
            transaction.Transaction,
            saving.Saving,
        ),
        'have': (bookkeeping.AccountWorth,),
        'types': (account.Account,),
    }
    return Accounts(GetData(conf)).table


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=saving.Saving)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_save, sender=transaction.SavingChange)
@receiver(post_delete, sender=transaction.SavingChange)
@receiver(post_save, sender=bookkeeping.SavingWorth)
def savings_signal(sender: object, instance: object, *args, **kwargs):
    data = savings_data()
    categories = get_categories(saving.SavingType)
    objects = create_objects(saving.SavingBalance, categories, data)
    save_objects(saving.SavingBalance, objects)


def savings_data():
    conf = {
        'incomes': (
            saving.Saving,
            transaction.SavingChange,
        ),
        'expenses': (
            transaction.SavingClose,
            transaction.SavingChange,
        ),
        'have': (bookkeeping.SavingWorth,),
        'types': (saving.SavingType,),
    }
    return Savings(GetData(conf)).table


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=pension.Pension)
@receiver(post_delete, sender=pension.Pension)
@receiver(post_save, sender=bookkeeping.PensionWorth)
def pensions_signal(sender: object, instance: object, *args, **kwargs):
    data = pensions_data()
    categories = get_categories(pension.PensionType)
    objects = create_objects(pension.PensionBalance, categories, data)
    save_objects(pension.PensionBalance, objects)


def pensions_data():
    conf = {
        'incomes': (pension.Pension,),
        'have': (bookkeeping.PensionWorth,),
        'types': (pension.PensionType,),
    }
    return Savings(GetData(conf)).table


def get_categories(model: Model) -> dict:
    return {category.id: category for category in model.objects.related()}


def create_objects(balance_model: Model, categories: dict, data: list[dict]):
    fields = balance_model._meta.get_fields()
    fk_field = [f.name for f in fields if (f.many_to_one)][0]
    objects = []
    for x in data:
        # extract account/saving_type/pension_type id from dict
        cid = x.pop('id')
        # drop latest_check if empty
        if not x['latest_check']:
            x.pop('latest_check')
        # create fk_field account|saving_type|pension_type object
        x[fk_field] = categories.get(cid)
        # create AccountBalance/SavingBalance/PensionBalance object
        objects.append(balance_model(**x))
    return objects


def save_objects(balance_model, objects):
    # delete all records
    balance_model.objects.related().delete()
    # bulk create
    balance_model.objects.bulk_create(objects)


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
        self.types = self._get_data(self.conf.get('types'), 'items')

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

    def _insert_future_data(self, df: DF) -> DF:
        # last year in dataframe
        year = df.index.levels[1].max()
        # get last group of (year, id)
        last_group = df.groupby(['year', 'id']).last().loc[year]
        return self._reset_values(year + 1, df, last_group)

    def _insert_missing_types(self, df: DF) -> DF:
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
        # copy types (account) from previous to current year
        df = self._insert_missing_types(df)
        # insert extra group for future year
        df = self._insert_future_data(df)
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
        # copy types (saving_type or pension_type) from previous to current year
        df = self._insert_missing_types(df)
        # data for one year +
        df = self._insert_future_data(df)
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
