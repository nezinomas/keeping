import contextlib
import itertools as it
from dataclasses import dataclass, field

import pandas as pd
from django.apps import apps
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from pandas import DataFrame as DF

from ..bookkeeping import models as worth
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
@receiver(post_save, sender=expense.Expense)
@receiver(post_save, sender=saving.Saving)
@receiver(post_save, sender=transaction.Transaction)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_save, sender=debt.Debt)
@receiver(post_save, sender=debt.DebtReturn)
@receiver(post_save, sender=worth.AccountWorth)
def accounts_post_save(sender: object,
                       instance: object,
                       *args,
                       **kwargs):
    created = kwargs.get('created')
    SignalBase.accounts(sender, instance, created, 'save')


@receiver(post_delete, sender=income.Income)
@receiver(post_delete, sender=expense.Expense)
@receiver(post_delete, sender=saving.Saving)
@receiver(post_delete, sender=transaction.Transaction)
@receiver(post_delete, sender=transaction.SavingClose)
@receiver(post_delete, sender=debt.Debt)
@receiver(post_delete, sender=debt.DebtReturn)
def accounts_post_delete(sender: object,
                         instance: object,
                         *args,
                         **kwargs):
    created = kwargs.get('created')
    SignalBase.accounts(sender, instance, created, 'delete')


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=saving.Saving)
@receiver(post_save, sender=transaction.SavingClose)
@receiver(post_save, sender=transaction.SavingChange)
@receiver(post_save, sender=worth.SavingWorth)
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
@receiver(post_save, sender=worth.PensionWorth)
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

    def _get_data(self, hooks: tuple, method: str):
        # hooks tuple: (app.model)
        items = []
        for m in hooks:
            try:
                model = apps.get_model(m)
            except LookupError:
                continue

            with contextlib.suppress(AttributeError):
                _method = getattr(model.objects, method)
                if _qs := _method():
                    items.extend(_qs)
        return items


class Accounts:
    _df = pd.DataFrame()
    _have = pd.DataFrame()

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
