from abc import ABC, abstractmethod
from typing import Dict

from django.apps import apps
from pandas import DataFrame as DF
from pandas import Series


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
            'transactions.Transaction',
            'debts.Borrow',
            'debts.BorrowReturn',
            'debts.Lent',
            'debts.LentReturn',
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


def get_sql(year, model, method_name):
    qs = None

    try:
        method = getattr(model.objects, method_name)
        qs = method(year)
    except AttributeError:
        pass

    return qs


def collect_summary_data(year: int,
                         types: Dict[str, int],
                         where: ModelsAbstract) -> DF:

    qs = []
    df = _create_df(types)
    _models = where.models()

    for m in _models:
        model = apps.get_model(m)
        for name in ['summary', 'summary_from', 'summary_to']:
            q = get_sql(year, model, name)
            if q:
                qs.append(q)

    df_index_list = df.index.tolist()

    for q in qs:
        for row in q:
            try:
                title = row['title']
            except KeyError:
                break

            for k, v in row.items():
                if k in ('title', 'id'):
                    continue

                # copy values from qs to df
                if title in df_index_list:
                    try:
                        v = float(v)
                    except TypeError:
                        v = 0.0

                    df.at[title, k] = v

    return df


def _create_df(qs: Dict[str, int]) -> DF:
    df = DF()

    if len(qs) >= 1:
        df = _create_columns()
        df['title'] = Series([*qs.keys()])  # copy list of titles to df
        df['id'] = Series([*qs.values()])  # copy list of id to df
        df = df.set_index('title')
        df.fillna(0.0, inplace=True)

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
        'borrow_past', 'borrow_now',
        'borrow_return_past', 'borrow_return_now',
        'lent_past', 'lent_now',
        'lent_return_past', 'lent_return_now',
    ])

    return df
