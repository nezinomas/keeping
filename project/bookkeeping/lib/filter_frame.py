import pandas as pd


class FilterDf(object):
    def __init__(self, year, data):
        if not isinstance(data, dict):
            raise Exception('Wrong data format: data not dictionary.')

        self._year = year
        self._data = data

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
    def savings_worth(self):
        return self._filter_latest('savingworth')

    @property
    def savings_past(self):
        return self._filter_df('saving', 'lt')

    @property
    def trans_from(self):
        _df = self._filter_df('transaction', 'eq')
        _df = self._copy_column(_df, 'from_account', 'account')
        return _df

    @property
    def trans_from_past(self):
        _df = self._filter_df('transaction', 'lt')
        _df = self._copy_column(_df, 'from_account', 'account')
        return _df

    @property
    def trans_to(self):
        _df = self._filter_df('transaction', 'eq')
        _df = self._copy_column(_df, 'to_account', 'account')
        return _df

    @property
    def trans_to_past(self):
        _df = self._filter_df('transaction', 'lt')
        _df = self._copy_column(_df, 'to_account', 'account')
        return _df

    @property
    def savings_close_from_past(self):
        _df = self._filter_df('savingclose', 'lt')
        _df = self._copy_column(_df, 'from_account', 'account')
        _df = self._copy_column(_df, 'from_account', 'saving_type')
        return _df

    @property
    def savings_close_to_past(self):
        _df = self._filter_df('savingclose', 'lt')
        _df = self._copy_column(_df, 'to_account', 'account')
        return _df

    @property
    def savings_close_from(self):
        _df = self._filter_df('savingclose', 'eq')
        _df = self._copy_column(_df, 'from_account', 'account')
        _df = self._copy_column(_df, 'from_account', 'saving_type')
        return _df

    @property
    def savings_close_to(self):
        _df = self._filter_df('savingclose', 'eq')
        _df = self._copy_column(_df, 'to_account', 'account')
        return _df

    @property
    def savings_change_from_past(self):
        _df = self._filter_df('savingchange', 'lt')
        _df = self._copy_column(_df, 'from_account', 'saving_type')
        return _df

    @property
    def savings_change_to_past(self):
        _df = self._filter_df('savingchange', 'lt')
        _df = self._copy_column(_df, 'to_account', 'saving_type')
        return _df

    @property
    def savings_change_from(self):
        _df = self._filter_df('savingchange', 'eq')
        _df = self._copy_column(_df, 'from_account', 'saving_type')
        return _df

    @property
    def savings_change_to(self):
        _df = self._filter_df('savingchange', 'eq')
        _df = self._copy_column(_df, 'to_account', 'saving_type')
        return _df

    def _filter_df(self, model_name, action):
        df = self._data.get(model_name)

        if not isinstance(df, pd.DataFrame):
            return

        if action == 'lt':
            df = df[df['date'].dt.year.lt(self._year)]

        if action == 'eq':
            df = df[df['date'].dt.year.eq(self._year)]

        return df

    def _filter_latest(self, model_name):
        df = self._data.get(model_name)

        if not isinstance(df, pd.DataFrame):
            return

        # get id of rows with latest records
        idx = df.groupby(by='saving_type')['date'].idxmax()

        return df.loc[idx]

    def _copy_column(self, df, old_name, new_name):
        if not isinstance(df, pd.DataFrame):
            return df

        df[new_name] = df[old_name]

        return df
