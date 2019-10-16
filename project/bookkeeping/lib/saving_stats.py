import pandas as pd

from ...core.mixins.calc_balance import BalanceStats
from .helpers import calc_percent, calc_sum


class SavingStats(BalanceStats):
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

    def __init__(self, stats, worth, saving_type='all'):
        self._balance = pd.DataFrame()
        self._type = saving_type

        if not isinstance(stats, pd.DataFrame):
            return

        if stats.empty:
            return

        df = self._prepare(stats)
        df = self._calc_balance(df)
        df = self._have(df, worth)
        df = self._profit(df)
        df = self._drop_columns(df)

        self._balance = df

    @property
    def totals(self):
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
    def total_market(self):
        t = self.totals

        return t.get('market_value', 0.0)

    # remove rows dependinf from saving_type
    def _filter_df(self, df):
        if self._type == 'all':
            return df

        df = df.reset_index()

        _filter = df['title'].str.contains('pensij', case=False)

        df = df[~_filter] if self._type == 'fund' else df
        df = df[_filter] if self._type == 'pension' else df

        df.set_index('title', inplace=True)

        return df

    def _prepare(self, stats: pd.DataFrame) -> pd.DataFrame:
        for col in self._columns:
            stats.loc[:, col] = 0.0

        return stats

    def _calc_balance(self, df: pd.DataFrame) -> pd.DataFrame:
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
            + df['s_change_to_fee_past']
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
            + df['s_change_to_fee_now']
            + df['s_change_from_fee_now']
        )

        df['invested'] = df['incomes'] - df['fees']

        return df

    def _have(self, df, worth):
        # join savings and worth dataframes
        if worth:
            _worth = pd.DataFrame(worth).set_index('title')
            df = df.join(_worth)
        else:
            df.loc[:, 'have'] = 0.0

        # filter df
        df = self._filter_df(df)

        # copy values from have to market_value
        df['market_value'] = df['have']

        return df

    def _profit(self, df: pd.DataFrame) -> pd.DataFrame:
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

    def _drop_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[self._columns]
