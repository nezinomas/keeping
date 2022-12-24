from datetime import date

import janitor
import pandas as pd
from pandas import DataFrame as DF


class MakeDataFrame:
    def __init__(self, year: int, data: list[dict], types: list, month: int = None):
        self.year = year
        self.month = month
        self.expenses = self.create_expenses(data, types)
        self.exceptions = self.create_exceptions(data)

    def create_expenses(self, data: list[dict], types: list) -> DF:
        df = self._df(data, 'sum')
        df = self._insert_missing_column(df, types)
        df = self._insert_missing_dates(df)
        return df.set_index('date')

    def create_exceptions(self, data: list[dict]) -> DF:
        df = self._df(data, 'exception_sum')
        df = self._insert_missing_dates(df)
        df.loc[:, 'sum'] = df.sum(axis=1, numeric_only=True)
        return df.set_index('date').select_columns(['sum'])

    def _df(self, data, sum_column: str) -> DF:
        df = self._create(data, sum_column)
        df = self._group_and_sum(df, sum_column)
        df = self._transform(df)
        return df

    def _create(self, data: list[dict], sum_column) -> DF:
        # make dataframe and convert dates, decimals
        df = DF(data).select_columns(['date', 'title', sum_column]).to_datetime('date')
        df[sum_column] = df[sum_column].apply(pd.to_numeric, downcast='float')
        return df

    def _group_and_sum(self, df: DF, sum_column: str) -> DF:
        ''' Group by month or by day and sum selected column '''
        grp = df.date.dt.day if self.month else df.date.dt.month
        return df.groupby(['title', grp])[sum_column].sum()

    def _transform(self, df: DF) -> DF:
        df = df.unstack().reset_index().T.reset_index()
        df.columns = df.iloc[0] # first row values -> to columns names
        df = df.drop(0)  # remove first row
        df = df.rename(columns={'title': 'date'})  # rename column
        # convert date int value to datetime
        if self.month:
            def dt(day): return date(self.year, self.month, day)
        else:
            def dt(month): return date(self.year, month, 1)
        df['date'] = pd.to_datetime(df['date'].apply(dt))
        return df

    def _insert_missing_column(self, df: DF, types: list) -> DF:
        # create missing columns
        df[[*set(types) - set(df.columns)]] = 0.0
        # sort columns
        return df[sorted(df.columns)]

    def _insert_missing_dates(self, df: DF) -> DF:
        ''' Insert missing months or days into DataFrame '''
        if self.month:
            tm = pd.Timestamp(self.year, self.month, 1)
            rng = pd.date_range(
                start=tm, end=(tm + pd.offsets.MonthEnd(0)), freq='D')
        else:
            rng = pd.date_range(f'{self.year}', periods=12, freq='MS')

        return df.complete({'date': rng}, fill_value=0.0)
