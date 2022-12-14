import contextlib
import itertools as it
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field

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
    }
    return Savings(GetData(conf)).table


def get_categories(model: Model) -> dict:
    return {category.id: category for category in model.objects.related()}


def create_objects(balance_model: Model, categories: dict, data: list[dict]):
    fields = balance_model._meta.get_fields()
    fk_field = [f.name for f in fields if (f.many_to_one)][0]
    objects = []
    for x in data:
        # extrack account/saving_type/pension_type id from dict
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

    def __post_init__(self):
        self.incomes = self._get_data(self.conf.get('incomes'), 'incomes')
        self.expenses = self._get_data(self.conf.get('expenses'), 'expenses')
        self.have = self._get_data(self.conf.get('have'), 'have')

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
        last_group = df.groupby(['year', 'id']).last().loc[year].reset_index()
        # insert column year with value year+1
        last_group['year'] = year + 1
        last_group.set_index(['id', 'year'], inplace=True)
        # set incomes, expenses | fee columns values to 0
        last_group[['incomes', 'expenses']] = 0.0
        if 'fee' in last_group.columns:
            last_group[['fee']] = 0.0
        # join dataframes
        df = pd.concat([df, last_group])
        return df.sort_index()


class Accounts(SignalBase):
    def __init__(self, data: GetData):
        _df = self._make_df(data.incomes, data.expenses)
        _hv = self._make_have(data.have)

        self._table = self._make_table(_df, _hv)

    def _make_df(self, incomes: list[dict], expenses: list[dict]) -> DF:
        col_idx = [
            'id',
            'year',
        ]
        col_num = [
            'past',
            'incomes',
            'expenses',
            'balance',
            'delta',
        ]
        # create df from incomes and expenses
        df = pd.DataFrame(it.chain(incomes, expenses))

        if df.empty:
            return pd.DataFrame(columns=col_idx + col_num).set_index(col_idx)

        # create missing columns
        df[[*set(col_num) - set(df.columns)]] = 0.0
        # convert decimal to float
        df[col_num] = df[col_num].astype(float)
        # groupby id, year and sum
        df = df.groupby(col_idx)[col_num].sum(numeric_only=True)

        return df

    def _make_table(self, df: DF, hv: DF) -> DF:
        df = df.copy()
        hv = hv.copy()
        # concat df and have; fillna
        df = pd.concat([df, hv], axis=1).fillna(0.0)
        if df.empty:
            return df
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


class Savings(SignalBase):
    def __init__(self, data: GetData):
        _in = self._make_df(data.incomes)
        _ex = self._make_df(data.expenses)
        _hv = self._make_have(data.have)

        self._table = self._make_table(_in, _ex, _hv)

    def _make_df(self, arr: list[dict]) -> DF:
        col_idx = [
            'id',
            'year',
        ]
        col_num = [
            'incomes',
            'expenses',
            'fee',
        ]
        # create df from incomes and expenses
        df = pd.DataFrame(arr)

        if df.empty:
            return pd.DataFrame(columns=col_idx + col_num).set_index(col_idx)

        # create missing columns
        df[[*set(col_num) - set(df.columns)]] = 0.0
        # convert decimal to float
        df[col_num] = df[col_num].astype(float)
        # groupby id, year and sum
        df = df.groupby(col_idx)[col_num].sum(numeric_only=True)

        return df

    def _join_df(self, inc: DF, exp: DF, hv: DF) -> DF:
        # drop expenses column, rename fee
        inc.drop(columns=['expenses'], inplace=True)
        inc.rename(columns={'fee': 'fee_inc'}, inplace=True)
        # drop incomes column, rename fee
        exp.drop(columns=['incomes'], inplace=True)
        exp.rename(columns={'fee': 'fee_exp'}, inplace=True)
        # concat dataframes, sum fees
        df = pd.concat([inc, exp, hv], axis=1).fillna(0.0)
        df['fee'] = df.fee_inc + df.fee_exp
        # rename have -> market_value
        df.rename(columns={'have': 'market_value'}, inplace=True)
        # create columns
        cols = [
            'past_amount', 'past_fee',
            'per_year_incomes', 'per_year_fee',
            'invested',
            'profit_invested_proc', 'profit_invested_sum']
        df[cols] = 0.0
        # drop tmp columns
        df.drop(columns=['fee_inc', 'fee_exp'], inplace=True)
        return df

    def _make_table(self, inc: DF, exp: DF, hv: DF) -> DF:
        df = self._join_df(inc, exp, hv)
        if df.empty:
            return df

        df = self._insert_future_data(df)
        # calculate incomes
        df.per_year_incomes = df.incomes - df.expenses
        df.per_year_fee = df.fee
        # calculate past_amount
        df['tmp1'] = df.groupby("id")['per_year_incomes'].cumsum()
        df.past_amount = df.groupby("id")['tmp1'].shift(fill_value=0.0)
        # calculate past_fee
        df['tmp2'] = df.groupby("id")['per_year_fee'].cumsum()
        df.past_fee = df.groupby("id")['tmp2'].shift(fill_value=0.0)
        # recalculate incomes and fees with past values
        df.incomes = df.past_amount + df.per_year_incomes
        df.fee = df.past_fee + df.per_year_fee
        # calculate invested, invested cannot by negative
        df.invested = df.incomes - df.fee
        df.invested = df.invested.mask(df.invested < 0, 0.0)
        # calculate profit/loss
        df.profit_invested_sum = df.market_value - df.invested
        df.profit_invested_proc = \
            df[['market_value', 'invested']].apply(Savings.calc_percent, axis=1)
        # drop tmp columns
        df.drop(columns=['expenses', 'tmp1', 'tmp2'], inplace=True)

        return df

    @staticmethod
    def calc_percent(args):
        market = args[0]
        invested = args[1]

        rtn = 0.0
        if invested:
            rtn = ((market * 100) / invested) - 100

        return rtn
