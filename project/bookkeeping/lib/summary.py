from typing import List

import pandas as pd

from ...accounts.models import Account


def collect_summary_data(year: int, models: List) -> pd.DataFrame:
    df = _create_df_from_accounts()

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
                        df.at[idx, k] = v
    return df


def _create_df_from_accounts():
    df = pd.DataFrame()
    qs = Account.objects.all().values_list('title', flat=True)

    if qs:
        df = pd.DataFrame(qs, columns=['account']).set_index('account')

    return df
