from functools import reduce

import pandas as pd
from pandas import DataFrame as DF

from ...bookkeeping.lib import helpers as calc
from ...core.lib.balance_base import BalanceBase


class BalanceNew(BalanceBase):
    _columns = ['past', 'incomes', 'expenses', 'balance', 'have', 'delta']

    def __init__(self, year=None, data=None):
        """
        Args:
            year (int, optional):  Defaults to None.
            data (List[Dict]], optional): Defaults to None.

            data format:
            [{'id': int, 'year': int, 'field_name': Decimal}]

            id == account_id

            field_name == incomes/expenses/have
        """

        self._balance = DF()
        self._year = year

        if not data:
            return

        df = self._create_df(data)
        df = self._calc_balance(df)

        self._balance = df

    @property
    def year_account_link(self):
        rtn = {}

        if self._balance.empty:
            return rtn

        df = self._balance.copy()
        df.reset_index(inplace=True)
        df.set_index(['account_id', 'year'], inplace=True)

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
        df.set_index(['year', 'account_id'], inplace=True)

        return df

    @property
    def total_row(self):
        if self._balance.empty:
            return {}

        year = self._balance.index.max() if not self._year else self._year

        arr = self._balance.loc[year]

        return arr.sum().to_dict()

    @property
    def balance_start(self) -> float:
        return self.total_row.get('past', 0.0)

    @property
    def balance_end(self) -> float:
        return self.total_row.get('balance', 0.0)

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
        diff = list(set(self._columns) - set(_columns))

        if diff:
            for _column_name in diff:
                df[_column_name] = 0.0

        return df

    def _calc_balance(self, df):
        if not isinstance(df, DF):
            return {}

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

            # recalclate balance with past
            _df['balance'] = (
                _df[['past', 'incomes', 'expenses']].apply(calc.calc_balance, axis=1))
            _df['delta'] = _df[['have', 'balance']].apply(calc.calc_delta, axis=1)

            _arr.append(_df)

        df = reduce(lambda a, b: a.append(b), _arr)

        return df
