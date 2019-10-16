import pandas as pd
from ...core.mixins.calc_balance import BalanceStats


class AccountStats(BalanceStats):
    def __init__(self, account_stats, account_worth):
        self._balance = pd.DataFrame()

        if not isinstance(account_stats, pd.DataFrame):
            return

        if account_stats.empty:
            return

        self._calc_balance(account_stats)
        self._join_worth(account_worth)
        self._have()
        self._drop_columns()

    @property
    def balance_start(self):
        t = super().totals

        return t.get('past', 0.0)

    @property
    def balance_end(self):
        t = super().totals

        return t.get('balance', 0.0)

    def _calc_balance(self, df: pd.DataFrame) -> None:
        df.loc[:, 'past'] = 0.0
        df.loc[:, 'incomes'] = 0.0
        df.loc[:, 'expenses'] = 0.0
        df.loc[:, 'balance'] = 0.0

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

        self._balance = df

    def _join_worth(self, account_worth):
        if account_worth:
            _worth = pd.DataFrame(account_worth).set_index('title')
            _worth = _worth.apply(pd.to_numeric)
            self._balance = self._balance.join(_worth)
        else:
            self._balance.loc[:, 'have'] = 0.0

    def _have(self):
        self._balance.loc[:, 'delta'] = (
            self._balance['have'] - self._balance['balance']
        )

    def _drop_columns(self) -> None:
        self._balance = self._balance[
            ['past', 'incomes', 'expenses', 'balance', 'have', 'delta']
        ]

