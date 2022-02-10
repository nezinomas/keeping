from functools import reduce

import pandas as pd
from pandas import DataFrame as DF

from ...bookkeeping.lib import helpers as calc
from ...core.lib.balance_base import BalanceBase


class Balance(BalanceBase):
    def __init__(self, year=None):
        self._balance = DF()
        self._year = year

    @classmethod
    def accounts(cls, year=None):
        cls.id_field = 'account_id'
        cls.calc_balance_method_name = '_calc_account_balance'
        cls.columns = [
            'past',
            'incomes',
            'expenses',
            'balance',
            'have',
            'delta'
        ]

        return cls(year)

    @classmethod
    def savings(cls, year=None):
        cls.id_field = 'saving_type_id'
        cls.calc_balance_method_name = '_calc_saving_balance'
        cls.columns = [
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

        return cls(year)

    @property
    def year_account_link(self):
        rtn = {}

        if self._balance.empty:
            return rtn

        df = self._balance.copy()
        df.reset_index(inplace=True)
        df.set_index([self.id_field, 'year'], inplace=True)

        idx = df.index.to_list()
        for r in idx:
            _id = r[0]
            _year = r[1]

            if not rtn.get(_year):
                rtn[_year] = []

            rtn[_year].append(_id)

        return rtn

    @property
    def balance_df(self):
        if self._balance.empty:
            return self._balance

        df = self._balance.copy()

        df.reset_index(inplace=True)
        df.set_index(['year', self.id_field], inplace=True)

        return df

    @property
    def total_row(self):
        if self._balance.empty:
            return {}

        year = self._balance.index.max() if not self._year else self._year

        arr = self._balance.loc[year]
        arr = arr.sum()

        # update values for saving/pension
        if not self.id_field == 'account_id':
            arr['profit_incomes_proc'] = (
                calc.calc_percent(arr[['market_value', 'incomes']])
            )
            arr['profit_invested_proc'] = (
                calc.calc_percent(arr[['market_value', 'invested']])
            )

        return arr.to_dict()

    @property
    def balance_start(self) -> float:
        return self.total_row.get('past', 0.0)

    @property
    def balance_end(self) -> float:
        return self.total_row.get('balance', 0.0)

    @property
    def total_market(self) -> float:
        t = self.total_row

        return t.get('market_value', 0.0)

    def create_balance(self, data):
        """
        Args:
            data (List[Dict]], optional): Defaults to None.

            data format:
            [{'id': int, 'year': int, 'field_name': Decimal}]

            id == account_id

            field_name == incomes/expenses/have
        """

        if not data:
            return

        df = self._create_df(data)
        df = getattr(self, self.calc_balance_method_name)(df)

        self._balance = df

    def _create_df(self, data):
        _arr = []

        for qs in data:
            _df = pd.DataFrame(qs)

            try:
                _df.set_index(['id', 'year'], inplace=True)
            except KeyError:
                continue

            # convert Decimal to float64
            _columns = _df.columns.to_list()
            _df[_columns] = _df[_columns].apply(pd.to_numeric)

            _arr.append(_df)

        if not _arr:
            return

        df = reduce(lambda a, b: a.add(b, fill_value=0), _arr)

        # fill NaN with 0.0
        df.fillna(0, inplace=True)

        # create columns if not exists
        _columns = df.columns.to_list()
        diff = list(set(self.columns) - set(_columns))

        if diff:
            for _column_name in diff:
                df[_column_name] = 0.0

        return df

    def _calc_account_balance(self, df):
        if not isinstance(df, DF):
            return {}

        df.sort_index(inplace=True)

        _arr = []

        # account_id list from df index.level[0]
        idx = df.index.unique(level=0).to_list()
        for account_id in idx:
            # filter df by account_id
            _df =  df.loc[account_id, :].copy()

            # new column with account_id value
            _df['account_id'] = account_id

            # calc balance without past
            _df['balance'] = _df['incomes'] - _df['expenses']

            # get past values
            # shift balance values down one row
            _df['past'] = _df.balance.shift(periods=1, fill_value=0.0)

            _df = Balance.recalc_accounts(_df)

            _arr.append(_df)

        df = reduce(lambda a, b: a.append(b), _arr)

        return df

    @staticmethod
    def recalc_accounts(_df):
        # recalclate balance with past
        _df['balance'] = (_df[['past', 'incomes', 'expenses']].apply(calc.calc_balance, axis=1))
        _df['delta'] = _df[['have', 'balance']].apply(calc.calc_delta, axis=1)

        return _df

    def _calc_saving_balance(self, df):
        if not isinstance(df, DF):
            return {}

        df.sort_index(inplace=True)

        _arr = []

        # if no expenses column create it
        if not 'expenses' in df.columns.to_list():
            df['expenses'] = 0.0

        if not 'have' in df.columns.to_list():
            df['have'] = 0.0

        # account_id list from df index.level[0]
        idx = df.index.unique(level=0).to_list()
        for account_id in idx:
            # filter df by account_id
            _df =  df.loc[account_id, :].copy()

            # new column with account_id value
            _df[self.id_field] = account_id

            # copy values from have to market_value
            _df['market_value'] = _df['have']

            # calculate incomes
            _df['incomes'] = _df['incomes'] - _df['expenses']

            # # get past values
            # shift free and incomes values down one row
            _df['past_amount'] = _df.incomes.shift(periods=1, fill_value=0.0)
            _df['past_fee'] = _df.fees.shift(periods=1, fill_value=0.0)

            _df = Balance.recalc_savings(_df)


            _arr.append(_df)

        df = reduce(lambda a, b: a.append(b), _arr)

        # delete expenses column
        df.drop(['expenses', 'have'], axis=1, inplace=True)

        return df

    @staticmethod
    def recalc_savings(_df):
        # recalclate balance with past
        # recalclate incomes and fees with past
        _df['incomes'] = _df['past_amount'] + _df['incomes']
        _df['fees'] = _df['past_fee'] + _df['fees']

        _df['invested'] = _df['incomes'] - _df['fees']

        # invested sum cannot be negative
        _df['invested'] = _df['invested'].mask(_df['invested'] < 0, 0.0)

        # # calc profit/loss sum and %
        _df['profit_incomes_sum'] = _df['market_value'] - _df['incomes']
        _df['profit_invested_sum'] = _df['market_value'] - _df['invested']

        _df['profit_incomes_proc'] = (
            _df[['market_value', 'incomes']]
            .apply(calc.calc_percent, axis=1)
        )

        _df['profit_invested_proc'] = (
            _df[['market_value', 'invested']]
            .apply(calc.calc_percent, axis=1)
        )

        return _df
