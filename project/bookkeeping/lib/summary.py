from typing import List

import pandas as pd

from ...accounts.models import Account
from ...savings.models import SavingType


def collect_summary_data(year: int, models: List) -> pd.DataFrame:
    df_account = _create_df_from_accounts()
    df_saving_type = _create_df_from_saving_type()

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

    return (df_account, df_saving_type)


def _create_df_from_accounts():
    df = pd.DataFrame()
    qs = Account.objects.all().values_list('title', flat=True)

    if qs:
        df = pd.DataFrame(qs, columns=['account']).set_index('account')

    return df


def _create_df_from_saving_type():
    df = pd.DataFrame()
    qs = SavingType.objects.all().values_list('title', flat=True)

    if qs:
        df = pd.DataFrame(qs, columns=['saving_type']).set_index('saving_type')

    return df
