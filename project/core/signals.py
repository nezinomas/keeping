import contextlib
import itertools as it
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
from .signals_base import SignalBase


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
    save_objects(account.Account, account.AccountBalance, data, categories, objects)


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
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_save, sender=transaction.SavingChange)
@receiver(post_save, sender=bookkeeping.SavingWorth)
def savings_post_save(sender: object,
                      instance: object,
                      *args,
                      **kwargs):
    created = kwargs.get('created')
    SignalBase.savings(sender, instance, created, 'save')


@receiver(post_delete, sender=saving.Saving)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_delete, sender=transaction.SavingChange)
def savings_post_delete(sender: object,
                        instance: object,
                        *args,
                        **kwargs):
    created = kwargs.get('created')
    SignalBase.savings(sender, instance, created, 'delete')


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=pension.Pension)
@receiver(post_save, sender=bookkeeping.PensionWorth)
def pensions_post_save(sender: object,
                       instance: object,
                       *args,
                       **kwargs):
    created = kwargs.get('created')
    SignalBase.pensions(sender, instance, created, 'save')


@receiver(post_delete, sender=pension.Pension)
def pensions_post_delete(sender: object,
                         instance: object,
                         *args,
                         **kwargs):
    created = kwargs.get('created')
    SignalBase.pensions(sender, instance, created, 'delete')


def get_categories(model: Model) -> dict:
    return {category.id: category for category in model.objects.related()}


def create_objects(balance_model: Model, categories: dict, data: list[dict]):
    objects = []
    for x in data:
        # extrack account/saving_type/pension_type id from dict
        cid = x.pop('id')
        # drop latest_check if empty
        if not x['latest_check']:
            x.pop('latest_check')
        # create AccountBalance/SavingBalance/PensionBalance object
        obj = balance_model(account=categories.get(cid), **x)
        objects.append(obj)
    return objects


def save_objects(categories_model, balance_model, data, categories, objects):
    # delete all records
    account.AccountBalance.objects.related().delete()
    # bulk create
    account.AccountBalance.objects.bulk_create(objects)


@dataclass
class GetData:
    conf: dict[tuple] = field(default_factory=dict)
    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    have: list[dict] = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = self._get_data(self.conf['incomes'], 'incomes')
        self.expenses = self._get_data(self.conf['expenses'], 'expenses')
        self.have = self._get_data(self.conf['have'], 'have')

    def _get_data(self, models: tuple, method: str):
        items = []
        for model in models:
            with contextlib.suppress(AttributeError):
                _method = getattr(model.objects, method)
                if _qs := _method():
                    items.extend(_qs)
        return items


class Accounts:
    def __init__(self, data: GetData):
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

    def _make_have(self, have: list[dict]) -> DF:
        hv = pd.DataFrame(have)
        idx = ['id', 'year']
        if hv.empty:
            cols = ['id', 'year', 'have', 'latest_check']
            return pd.DataFrame(columns=cols).set_index(idx)
        # set index
        hv.set_index(keys=idx, inplace=True)
        # convert Decimal -> float
        hv['have'] = hv['have'].astype(float)

        return hv

    def _make_table(self, df: DF, hv: DF) -> DF:
        df = df.copy()
        hv = hv.copy()
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


class Savings:
    def __init__(self, data: GetData):
        _in = self._make_df(data.incomes)
        _ex = self._make_df(data.expenses)
        _hv = self._make_have(data.have)

        self._table = self._make_table(_in, _ex, _hv)

    @property
    def table(self):
        df = self._table.copy().reset_index()

        return df.to_dict('records')

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

    def _make_have(self, have: list[dict]) -> DF:
        hv = pd.DataFrame(have)

        if hv.empty:
            idx = ['id', 'year']
            cols = ['id', 'year', 'have', 'latest_check']
            return pd.DataFrame(columns=cols).set_index(idx)

        hv['have'] = hv['have'].astype(float)
        hv.set_index(['id', 'year'], inplace=True)
        return hv

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
            'invested',
            'profit_incomes_proc', 'profit_incomes_sum',
            'profit_invested_proc', 'profit_invested_sum']
        df[cols] = 0.0
        # drop tmp columns
        df.drop(columns=['fee_inc', 'fee_exp'], inplace=True)
        return df

    def _make_table(self, inc: DF, exp: DF, hv: DF) -> DF:
        df = self._join_df(inc, exp, hv)
        # calculate incomes
        df.incomes = df.incomes - df.expenses
        # calculate past_amount
        df['tmp1'] = df.groupby("id")['incomes'].cumsum()
        df.past_amount = df.groupby("id")['tmp1'].shift(fill_value=0.0)
        # calculate past_fee
        df['tmp2'] = df.groupby("id")['fee'].cumsum()
        df.past_fee = df.groupby("id")['tmp2'].shift(fill_value=0.0)
        # recalculate incomes and fees with past values
        df.incomes = df.past_amount + df.incomes
        df.fee = df.past_fee + df.fee
        # calculate invested, invested cannot by negative
        df.invested = df.incomes - df.fee
        df.invested = df.invested.mask(df.invested < 0, 0.0)
        # calculate profit/loss
        df.profit_incomes_sum = df.market_value - df.incomes
        df.profit_invested_sum = df.market_value - df.invested
        df.profit_incomes_proc = \
            df[['market_value', 'incomes']].apply(Savings.calc_percent, axis=1)
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
