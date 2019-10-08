import pandas as pd

from ...core.mixins.calc_balance import BalanceStats
from .helpers import calc_percent, calc_sum


class SavingStats(BalanceStats):
    def __init__(self, stats, worth, saving_type='all'):
        self._balance = pd.DataFrame()
        self._type = saving_type

        if not stats or stats is None:
            return

        self._prepare_balance(stats, worth)
        self._calc_balance()

    @property
    def totals(self):
        val = {}

        if not isinstance(self._balance, pd.DataFrame):
            return val

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

    def _prepare_balance(self, stats, worth):
        df = pd.DataFrame(stats).set_index('title')

        # join savings and worth dataframes
        if worth:
            _worth = pd.DataFrame(worth).set_index('title')
            df = df.join(_worth)
        else:
            df.loc[:, 'have'] = 0.0

        # filter df
        df = self._filter_df(df)
        if df.empty:
            return self._balance

        # convert to float
        for col in df.columns:
            df.loc[:, col] = pd.to_numeric(df[col])

        # rename columns
        df.rename(columns={'have': 'market_value'}, inplace=True)

        # add columns
        df.loc[:, 'profit_incomes_proc'] = 0.00
        df.loc[:, 'profit_incomes_sum'] = 0.00
        df.loc[:, 'profit_invested_proc'] = 0.00
        df.loc[:, 'profit_invested_sum'] = 0.00

        self._balance = df

    def _calc_balance(self):
        if self._balance.empty:
            return self._balance

        # calculate percent of profit/loss
        self._balance['profit_incomes_proc'] = (
            self._balance[['market_value', 'incomes']]
            .apply(calc_percent, axis=1)
        )

        self._balance['profit_invested_proc'] = (
            self._balance[['market_value', 'invested']]
            .apply(calc_percent, axis=1)
        )

        # calculate sum of profit/loss
        self._balance['profit_incomes_sum'] = (
            self._balance[['market_value', 'incomes']]
            .apply(calc_sum, axis=1)
        )

        self._balance['profit_invested_sum'] = (
            self._balance[['market_value', 'invested']]
            .apply(calc_sum, axis=1)
        )
