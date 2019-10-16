import pandas as pd

from ...core.mixins.calc_balance import BalanceStats


class AccountStats(BalanceStats):
    _columns = ['past', 'incomes', 'expenses', 'balance', 'have', 'delta']

    def __init__(self, account_stats, account_worth):
        self._balance = pd.DataFrame()

        if not isinstance(account_stats, pd.DataFrame):
            return

        if account_stats.empty:
            return

        df = self._prepare(account_stats)
        df = self._calc_balance(df)
        df = self._join_worth(df, account_worth)
        df = self._have(df)
        df = self._drop_columns(df)

        self._balance = df

    @property
    def balance_start(self):
        t = super().totals

        return t.get('past', 0.0)

    @property
    def balance_end(self):
        t = super().totals

        return t.get('balance', 0.0)

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in self._columns:
            df.loc[:, col] = 0.0

        return df

    def _calc_balance(self, df: pd.DataFrame) -> None:
        df['past'] = (
            0
            + df['i_past']
            - df['e_past']
            - df['s_past']
            - df['tr_from_past']
            + df['tr_to_past']
            + df['s_close_to_past']
        )

        df['incomes'] = (
            0
            + df['i_now']
            + df['tr_to_now']
            + df['s_close_to_now']
        )

        df['expenses'] = (
            0
            - df['e_now']
            - df['s_now']
            - df['tr_from_now']
        ).abs()

        df['balance'] = (
            0
            + df['past']
            + df['incomes']
            - df['expenses']
        )

        return df

    def _join_worth(self, df: pd.DataFrame,
                    account_worth: pd.DataFrame) -> pd.DataFrame:
        if account_worth:
            _worth = pd.DataFrame(account_worth).set_index('title')
            _worth = _worth.apply(pd.to_numeric)
            df = df.join(_worth, lsuffix='have')

        return df

    def _have(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[:, 'delta'] = df['have'] - df['balance']
        return df

    def _drop_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[self._columns]
