from abc import ABC, abstractmethod
from typing import Dict

from django.apps import apps
from pandas import DataFrame as DF
from pandas import Series, to_numeric


class ModelsAbstract(ABC):
    @abstractmethod
    def models(self):
        pass


class AccountsBalanceModels(ModelsAbstract):
    @classmethod
    def models(cls):
        return [
            'incomes.Income',
            'expenses.Expense',
            'savings.Saving',
            'transactions.SavingClose',
            'transactions.Transaction'
        ]


class SavingsBalanceModels(ModelsAbstract):
    @classmethod
    def models(cls):
        return [
            'savings.Saving',
            'transactions.SavingClose',
            'transactions.SavingChange'
        ]


class PensionsBalanceModels(ModelsAbstract):
    @classmethod
    def models(cls):
        return [
            'pensions.Pension',
        ]


def collect_summary_data(year: int,
                         types: Dict[str, int],
                         where: ModelsAbstract) -> DF:
    df = _create_df(types)

    _models = where.models()
    for m in _models:
        model = apps.get_model(m)
        # try 3 methods from model.manager:
        # a) summary(year)
        # b) summary_from(year)
        # c) summary_to(year)
        for i in ['', '_from', '_to']:
            try:
                method = getattr(model.objects, f'summary{i}')
                qs = method(year)
            except Exception as e:
                continue

            for row in qs:
                idx = row.get('title')

                if not idx:
                    continue

                for k, v in row.items():
                    if k == 'title' or k == 'id':
                        continue

                    # copy values from qs to df
                    if idx in df.index:
                        df.at[idx, k] = v

    # fill NaN with 0.0
    df.fillna(0.0, inplace=True)

    # convert all columns to float
    df = df.apply(to_numeric)

    return df


def _create_df(qs: Dict[str, int]) -> DF:
    df = DF()

    if len(qs) >= 1:
        df = _create_columns()
        df['title'] = Series([*qs.keys()])  # copy list of titles to df
        df['id'] = Series([*qs.values()])  # copy list of id to df
        df = df.set_index('title')

    return df


def _create_columns() -> DF:
    df = DF(columns=[
        'id',
        'title',
        'i_past', 'i_now',
        'e_past', 'e_now',
        's_past', 's_now',
        's_fee_past', 's_fee_now',
        'tr_from_past', 'tr_from_now',
        'tr_to_past', 'tr_to_now',
        's_close_to_past', 's_close_to_now',
        's_close_from_past', 's_close_from_now',
        's_change_to_past', 's_change_to_now',
        's_change_from_past', 's_change_from_now',
        's_change_from_fee_past', 's_change_from_fee_now',
    ])

    return df
