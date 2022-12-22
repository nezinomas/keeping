from datetime import date

import janitor
import pandas as pd
from pandas import DataFrame as DF


class MakeDataFrame:
    def __init__(self, year: int, month: int = None):
        self.year = year
        self.month = month

    def create_data(self, data: list[dict], types: list, sum_column: str = 'sum') -> DF:
        df = DF(data).remove_columns(['exception_sum']).to_datetime('date')
        df[sum_column] = df[sum_column].apply(pd.to_numeric, downcast='float')

        df = self.group_and_sum(df, sum_column)
        # modifie df: unstack, transpose, row to col names
        df = df.unstack().reset_index().T.reset_index()
        df.columns = df.iloc[0] # first row values -> to columns names
        df = df.drop(0)  # remove first row
        df = df.rename(columns={'title': 'date'})  # rename column

        # create missing columns
        df[[*set(types) - set(df.columns)]] = 0.0
        df = df[sorted(df.columns)]

        df = self.insert_missing_dates(df)

        print(f'\nF >>>>>>\n{df}\n')
        return df

    def insert_missing_dates(self, df: DF) -> DF:
                # create missing rows
        if self.month:
            def dt(x): return date(self.year, self.month, x)
            tm = pd.Timestamp(self.year, self.month, 1)
            new_dates = {'date': pd.date_range(
                start=tm, end=(tm + pd.offsets.MonthEnd(0)), freq='D')}

        else:
            def dt(x): return date(self.year, x, 1)
            new_dates = {
                'date': pd.date_range(f'{self.year}', periods=12, freq='MS')}

        df['date'] = pd.to_datetime(df['date'].apply(dt))
        return df.complete(new_dates, fill_value=0.0).set_index('date')

    def group_and_sum(self, df: DF, sum_column: str) -> DF:
        # groupby month or day and sum
        grp = df.date.dt.day if self.month else df.date.dt.month

        return df.groupby(['title', grp])[sum_column].sum()
