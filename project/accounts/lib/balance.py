from typing import List

from pandas import DataFrame as DF

from ...bookkeeping.lib import helpers as calc
from ...core.lib.balance_base import BalanceBase


class Balance(BalanceBase):
    _columns = ['past', 'incomes', 'expenses', 'balance', 'have', 'delta']

    def __init__(self, data: DF, account_worth: List):
        self._balance = DF()

        if not isinstance(data, DF):
            return

        if data.empty:
            return

        df = self._prepare(data)
        df = self._calc_balance(df)
        df = self._join_worth(df, account_worth)
        df = self._calc_have(df)
        df = self._drop_columns(df)

        self._balance = df

    @property
    def balance_start(self) -> float:
        t = super().total_row

        return t.get('past', 0.0)

    @property
    def balance_end(self) -> float:
        t = super().total_row

        return t.get('balance', 0.0)

    def _prepare(self, df: DF) -> DF:
        for col in self._columns:
            df.loc[:, col] = 0.0

        return df

    def _calc_balance(self, df: DF) -> DF:
        df['past'] = (
            0
            + df['i_past']
            + df['tr_to_past']
            + df['s_close_to_past']
            - df['e_past']
            - df['s_past']
            - df['tr_from_past']
            - df['borrow_past']
            + df['borrow_return_past']
            + df['lent_past']
            - df['lent_return_past']
        )

        df['incomes'] = (
            0
            + df['i_now']
            + df['tr_to_now']
            + df['s_close_to_now']
            + df['lent_now']
            + df['borrow_return_now']
        )

        df['expenses'] = (
            0
            - df['e_now']
            - df['s_now']
            - df['tr_from_now']
            - df['lent_return_now']
            - df['borrow_now']
        ).abs()

        df['balance'] = (
            df[['past', 'incomes', 'expenses']].apply(calc.calc_balance, axis=1)
        )

        return df

    def _join_worth(self, df: DF, account_worth: List) -> DF:
        if account_worth:
            df_index_list = df.index.tolist()
            for row in account_worth:
                title = row.get('title')
                if title in df_index_list:
                    try:
                        val = float(row['have'])
                    except (ValueError, TypeError, KeyError):
                        val = 0.0

                    df.at[title, 'have'] = val
        return df

    def _calc_have(self, df: DF) -> DF:
        df.loc[:, 'delta'] = (
            df[['have', 'balance']].apply(calc.calc_delta, axis=1)
        )

        return df

    def _drop_columns(self, df: DF) -> DF:
        return df[[*self._columns, 'id']]
