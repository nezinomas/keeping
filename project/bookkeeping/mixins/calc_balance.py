from typing import Dict, List

import pandas as pd


class CalcBalanceMixin():
    def convert_to_df(self, year, list_):
        df = pd.DataFrame(list_)

        # convert to float and datetime.date
        for col in df.columns:
            if col == 'date':
                df[col] = pd.to_datetime(df[col])
            else:
                df[col] = pd.to_numeric(df[col])

        df.set_index(df.date, inplace=True)

        # create empty DataFrame object with index containing all months
        date_range = pd.date_range(f'{year}', periods=12, freq='MS')
        data = pd.DataFrame(date_range, columns=['date'])
        data.set_index('date', inplace=True)

        # concat two dataframes
        df = pd.concat([data, df], axis=1).fillna(0.0)
        df.drop(['date'], axis=1, inplace=True)

        return df

    def balance(self, df: pd.DataFrame) -> List[Dict]:
        val = []

        if not isinstance(df, pd.DataFrame):
            return val

        if df.empty:
            return val

        df.reset_index(inplace=True)
        val = df.to_dict('records')

        return val

    def average(self, df: pd.DataFrame) -> Dict[str, float]:
        val = {}

        if not isinstance(df, pd.DataFrame):
            return val

        if df.empty:
            return val

        # replace 0.0 to None
        # average will be calculated only for months with non zero values
        df.replace(0.0, pd.NaT, inplace=True)
        df = df.mean(skipna=True)

        val = df.to_dict()

        return val

    def totals(self, df: pd.DataFrame) -> Dict[str, float]:
        val = {}

        if not isinstance(df, pd.DataFrame):
            return val

        if df.empty:
            return val

        df = df.sum()
        val = df.to_dict()

        return val
