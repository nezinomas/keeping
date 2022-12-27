from datetime import date

import janitor  # this package integrates into pandas api
import pandas as pd
from pandas import DataFrame as DF


class MakeDataFrame:
    def __init__(self, year: int, data: list[dict], types: list, month: int = None):
        self.year = year
        self.month = month
        self._data = data
        self._types = types

    @property
    def data(self):
        return self.create_data(self._data, self._types)

    @property
    def exceptions(self):
        return self.create_exceptions(self._data)

    def create_data(self, data: list[dict], types: list) -> DF:
        df = self._create(data, 'sum')
        df = self._insert_missing_columns(df, types)
        df = self._insert_missing_dates(df)
        return df.set_index('date')

    def create_exceptions(self, data: list[dict]) -> DF:
        df = self._create(data, 'exception_sum')
        df = self._insert_missing_dates(df)
        df.loc[:, 'sum'] = df.sum(axis=1, numeric_only=True)
        return df.set_index('date').select_columns(['sum'])

    def _create(self, data, sum_column: str) -> DF:
        if not data:
            return DF(columns=['date'])

        df = self._init(data, sum_column)
        df = self._group_and_sum(df, sum_column)
        df = self._transform(df)
        return df

    def _init(self, data: list[dict], sum_column) -> DF:
        ''' Create DataFrame and convert dates, decimals '''
        df = DF(data).select_columns(['date', 'title', sum_column]).copy()
        df['date'] = pd.to_datetime(df['date'])
        df[sum_column] = df[sum_column].apply(pd.to_numeric, downcast='float')
        return df

    def _group_and_sum(self, df: DF, sum_column: str) -> DF:
        ''' Group by month or by day and sum selected column '''
        grp = df.date.dt.day if self.month else df.date.dt.month
        return df.groupby(['title', grp])[sum_column].sum()

    def _transform(self, df: DF) -> DF:
        ''' Transform DataFrame Columns to Rows.
            Convert date column int to datetime
        '''
        df = df.unstack().reset_index().T.reset_index()
        df.columns = df.iloc[0] # first row values -> to columns names
        df = df.drop(0)  # remove first row
        df = df.rename(columns={'title': 'date'})  # rename column
        # convert date int value to datetime
        def dt(val: int) -> date:
            month_day = (self.month, val) if self.month else (val, 1)
            return date(self.year, *month_day)
        df['date'] = pd.to_datetime(df['date'].apply(dt))
        return df

    def _insert_missing_columns(self, df: DF, types: list) -> DF:
        ''' Insert missing columns '''
        if not types:
            return df

        df[[*set(types) - set(df.columns)]] = 0.0
        return df[sorted(df.columns)]

    def _insert_missing_dates(self, df: DF) -> DF:
        ''' Insert missing months or days '''
        if self.month:
            tm = pd.Timestamp(self.year, self.month, 1)
            rng = pd.date_range(
                start=tm, end=(tm + pd.offsets.MonthEnd(0)), freq='D')
        else:
            rng = pd.date_range(f'{self.year}', periods=12, freq='MS')

        if df.empty:
            df['date'] = pd.Series(list(rng))
            df.fillna(0.0, inplace=True)
        else:
            df = df.complete({'date': rng}, fill_value=0.0)

        return df