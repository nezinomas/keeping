from typing import List

import pandas as pd

from ...accounts.models import Account
from ...savings.models import SavingType


def collect_summary_data(year: int, models: List) -> pd.DataFrame:
    df_account = _create_df(Account)
    df_saving_type = _create_df(SavingType)

    for model in models:
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
                    if k == 'title':
                        continue
                    else:
                        # copy values from qs to
                        # df_account or df_saving_type
                        if idx in df_account.index:
                            df_account.at[idx, k] = v

                        if idx in df_saving_type.index:
                            df_saving_type.at[idx, k] = v

    # fill NaN with 0.0
    df_account.fillna(0.0, inplace=True)
    df_saving_type.fillna(0.0, inplace=True)

    # convert all columns to float
    df_account = df_account.apply(pd.to_numeric)
    df_saving_type = df_saving_type.apply(pd.to_numeric)

    return (df_account, df_saving_type)


def _create_df(model) -> pd.DataFrame:
    df = pd.DataFrame()
    qs = model.objects.all().values_list('title', flat=True)

    if len(qs) >= 1:
        df = _create_columns()
        df['title'] = pd.Series(qs)
        df = df.set_index('title')

    return df


def _create_columns() -> pd.DataFrame:
    df = pd.DataFrame(columns=[
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
        's_change_to_fee_past', 's_change_to_fee_now',
        's_change_from_past', 's_change_from_now',
        's_change_from_fee_past', 's_change_from_fee_now',
    ])

    return df
