import pandas as pd


class FilterDf(object):
    def __init__(self, year, data):
        self._year = year

        self._accounts = data.get('account')

        _incomes = data.get('income')
        if not _incomes.empty:
            self._incomes = self._filter_df(_incomes, 'eq')
            self._incomes_past = self._filter_df(_incomes, 'lt')

        _expenses = data.get('expense')
        if not _expenses.empty:
            self._expenses = self._filter_df(_expenses, 'eq')
            self._expenses_past = self._filter_df(_expenses, 'lt')

        _savings = data.get('saving')
        if not _savings.empty:
            self._savings = self._filter_df(_savings, 'eq')
            self._savings_past = self._filter_df(_savings, 'lt')

        _trans = data.get('transaction')
        if not _trans.empty:
            self._trans_from = self._filter_trans(_trans, 'from_account', 'eq')
            self._trans_from_past = self._filter_trans(
                _trans, 'from_account', 'lt')

            self._trans_to = self._filter_trans(_trans, 'to_account', 'eq')
            self._trans_to_past = self._filter_trans(
                _trans, 'to_account', 'lt')

    @property
    def accounts(self):
        return self._accounts

    @property
    def incomes(self):
        return self._incomes

    @property
    def incomes_past(self):
        return self._incomes_past

    @property
    def expenses(self):
        return self._expenses

    @property
    def expenses_past(self):
        return self._expenses_past

    @property
    def savings(self):
        return self._savings

    @property
    def savings_past(self):
        return self._savings_past

    @property
    def trans_from(self):
        return self._trans_from

    @property
    def trans_from_past(self):
        return self._trans_from_past

    @property
    def trans_to(self):
        return self._trans_to

    @property
    def trans_to_past(self):
        return self._trans_to_past

    def _filter_df(self, df, action):
        if action == 'lt':
            df = df[df['date'].dt.year.lt(self._year)]

        if action == 'eq':
            df = df[df['date'].dt.year.eq(self._year)]

        return df

    def _filter_trans(self, df, column, action):
        _df = self._filter_df(df, action)

        _df = _df.loc[:, [column, 'price']]
        _df.rename({column: 'account'}, axis=1, inplace=True)

        return _df
