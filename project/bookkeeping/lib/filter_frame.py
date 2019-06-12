import pandas as pd


class FilterDf(object):
    def __init__(self, year, data):
        self._year = year
        self._data = data

    @property
    def accounts(self):
        return self._data.get('account')

    @property
    def saving_types(self):
        return self._data.get('savingtype')

    @property
    def incomes(self):
        return self._filter_df('income', 'eq')

    @property
    def incomes_past(self):
        return self._filter_df('income', 'lt')

    @property
    def expenses(self):
        return self._filter_df('expense', 'eq')

    @property
    def expenses_past(self):
        return self._filter_df('expense', 'lt')

    @property
    def savings(self):
        return self._filter_df('saving', 'eq')

    @property
    def savings_past(self):
        return self._filter_df('saving', 'lt')

    @property
    def trans_from(self):
        return self._filter_trans('transaction', 'from_account', 'eq')

    @property
    def trans_from_past(self):
        return self._filter_trans('transaction', 'from_account', 'lt')

    @property
    def trans_to(self):
        return self._filter_trans('transaction', 'to_account', 'eq')

    @property
    def trans_to_past(self):
        return self._filter_trans('transaction', 'to_account', 'lt')

    def _filter_df(self, model_name, action):
        df = self._data.get(model_name)

        if action == 'lt':
            df = df[df['date'].dt.year.lt(self._year)]

        if action == 'eq':
            df = df[df['date'].dt.year.eq(self._year)]

        return df

    def _filter_trans(self, model_name, column, action):
        _df = self._filter_df(model_name, action)

        _df = _df.loc[:, [column, 'price']]
        _df.rename({column: 'account'}, axis=1, inplace=True)

        return _df
