from typing import Dict

from pandas import DataFrame as DF

from ...bookkeeping.lib.helpers import calc_percent, calc_sum
from ...core.lib.balance_base import BalanceBase


class Balance(BalanceBase):
    _columns = [
        'past_amount',
        'past_fee',
        'fees',
        'invested',
        'incomes',
        'market_value',
        'profit_incomes_proc',
        'profit_incomes_sum',
        'profit_invested_proc',
        'profit_invested_sum'
    ]

    def __init__(self, stats: DF, worth: DF):
        self._balance = DF()

        if not isinstance(stats, DF):
            return

        if stats.empty:
            return

        df = self._prepare(stats)
        df = self._calc_balance(df)
        df = self._calc_have(df, worth)
        df = self._calc_profit(df)
        df = self._drop_columns(df)

        self._balance = df

    @property
    def total_row(self) -> Dict:
        val = {}

        if self._balance.empty:
            return val

        arr = self._balance.copy()

        arr = arr.sum()

        arr['profit_incomes_proc'] = (
            calc_percent(arr[['market_value', 'incomes']])
        )
        arr['profit_invested_proc'] = (
            calc_percent(arr[['market_value', 'invested']])
        )

        val = arr.to_dict()

        return val

    @property
    def total_market(self) -> float:
        t = self.total_row

        return t.get('market_value', 0.0)

    def _prepare(self, stats: DF) -> DF:
        for col in self._columns:
            stats.loc[:, col] = 0.0

        return stats

    def _calc_balance(self, df: DF) -> DF:
        df['past_amount'] = (
            0.0
            + df['s_past']
            + df['s_change_to_past']
            - df['s_change_from_past']
            - df['s_close_from_past']
        )

        df['past_fee'] = (
            0.0
            + df['s_fee_past']
            + df['s_change_from_fee_past']
        )

        df['incomes'] = (
            0.0
            + df['s_now']
            + df['past_amount']
            + df['s_change_to_now']
            - df['s_change_from_now']
            - df['s_close_from_now']
        )

        df['fees'] = (
            0.0
            + df['s_fee_now']
            + df['past_fee']
            + df['s_change_from_fee_now']
        )

        df['invested'] = df['incomes'] - df['fees']

        return df

    def _calc_have(self, df: DF, worth: DF) -> DF:
        df.loc[:, 'have'] = 0.0

        # join savings and worth dataframes
        if worth:
            df_index_list = df.index.tolist()
            for row in worth:
                title = row.get('title')
                if title in df_index_list:
                    try:
                        val = float(row['have'])
                    except (ValueError, TypeError, KeyError):
                        val = 0.0

                    df.at[title, 'have'] = val

        # copy values from have to market_value
        df['market_value'] = df['have']

        return df

    def _calc_profit(self, df: DF) -> DF:
        # calculate percent of profit/loss
        df['profit_incomes_proc'] = (
            df[['market_value', 'incomes']]
            .apply(calc_percent, axis=1)
        )

        df['profit_invested_proc'] = (
            df[['market_value', 'invested']]
            .apply(calc_percent, axis=1)
        )

        # calculate sum of profit/loss
        df['profit_incomes_sum'] = (
            df[['market_value', 'incomes']]
            .apply(calc_sum, axis=1)
        )

        df['profit_invested_sum'] = (
            df[['market_value', 'invested']]
            .apply(calc_sum, axis=1)
        )
        return df

    def _drop_columns(self, df: DF) -> DF:
        return df[[*self._columns, 'id']]
