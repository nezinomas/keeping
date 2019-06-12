import pandas as pd


class CalcBalance(object):
    def __init__(self, groupby_col, balance):
        self._balance = balance
        self._groupby_col = groupby_col

    def calc(self, df, action, target_col):
        df = self._group_and_sum(df)
        df = df[[self._groupby_col, 'price']].set_index(self._groupby_col)

        df_index = df.index.tolist()

        for account_title in df_index:
            _price = df.at[account_title, 'price']
            _target = (account_title, target_col)

            if action == '+':
                self._balance.at[_target] += _price

            if action == '-':
                self._balance.at[_target] -= _price

    def _group_and_sum(self, df):
        return (
            df.groupby([self._groupby_col])['price']
            .sum()
            .reset_index()
        )
