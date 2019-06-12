import pandas as pd


class CalcBalance(object):
    def __init__(self, groupby_col, balance):
        self._balance = balance
        self._groupby_col = groupby_col

    def calc(self, df, action, action_col, summed_col='price'):
        df = self._group_and_sum(df, summed_col)

        if not isinstance(df, pd.DataFrame):
            return

        df = df[[self._groupby_col, summed_col]].set_index(self._groupby_col)

        df_index = df.index.tolist()

        for index in df_index:
            _price = df.at[index, summed_col]
            _target = (index, action_col)

            if index not in self._balance.index:
                continue

            if action == '+':
                self._balance.at[_target] += _price

            if action == '-':
                self._balance.at[_target] -= _price

    def _group_and_sum(self, df, summed_col):
        _summed = None
        try:
            _summed = (
                df.groupby([self._groupby_col])[summed_col]
                .sum()
                .reset_index()
            )
        except:
            pass

        return _summed
