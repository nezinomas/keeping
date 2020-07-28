import calendar
from datetime import date
from typing import Dict, List

import pandas as pd
from ...core.exceptions import MethodInvalid

class Stats():
    def __init__(self, year: int = None, data: List[Dict[date, float]] = None):
        self._year = year
        self._df = self._prepare_df(data if data else [])

    @staticmethod
    def months():
        arr = [
            'Sausis',
            'Vasaris',
            'Kovas',
            'Balandis',
            'Gegužė',
            'Birželis',
            'Liepa',
            'Rugpjūtis',
            'Rugsėjis',
            'Spalis',
            'Lapkritis',
            'Gruodis'
        ]
        return arr

    @staticmethod
    def weekdays():
        return([
            'Pirmadienis',
            'Antradienis',
            'Trečiadienis',
            'Ketvirtadienis',
            'Penktadienis',
            'Šeštadienis',
            'Sekmadienis'
        ])

    def weekdays_stats(self):
        df = self._df.copy()

        if not df.empty:
            df['weekday'] = df['date'].dt.dayofweek

            df = df.groupby('weekday')['date'].count()

        df = df.to_dict() # {0: 1, 1: 0} == {weekday: counts, }

        # return list with zeros
        arr = []
        for i in range(0, 7):
            arr.append({'weekday': i, 'count': 0})

        # update return list with counts
        for k, v in df.items():
            arr[k]['count'] = v

        return arr

    def months_stats(self):
        df = self._df.copy()

        if not df.empty:
            df.loc[:, 'YearMonth'] = df['date'].dt.to_period('M').astype(str)

            df = df.groupby('YearMonth')['qty'].sum()

        df = df.reset_index().to_dict('records')

        arr = [0] * 12 # return list filled with zeros

        # copy values from DataFrame to list
        for row in df:
            key = int(row['YearMonth'][5:7])
            arr[key - 1] = row['qty']

        return arr

    def year_stats(self):
        if not self._year:
            raise MethodInvalid('class Stats must be called with specified year.')

        arr = self._empty_list()
        df = self._df.copy()

        if df.empty:
            return arr

        # time gap between days with records
        df['duration'] = df['date'].diff().dt.days
        first_record_date = df['date'].iloc[0]

        # repair time gap for first year record
        first_date = pd.to_datetime(f'{first_record_date.year}-01-01')
        first_duration = (first_record_date - first_date).days

        df.loc[df.index[0], 'duration'] = first_duration

        # copy values from DataFrame to arr
        for _, row in df.iterrows():
            month = row['date'].month
            day = row['date'].day

            arr[month - 1][day - 1]['y'] = row['qty']
            arr[month - 1][day - 1]['gap'] = row['duration']

        return arr

    def year_totals(self):
        df = self._df.copy()

        df = df.groupby(df['date'].dt.year)['qty'].sum()

        arr = df.to_dict()
        print(arr)
        if self._year:
            return arr.get(self._year, 0)
        else:
            return arr


    def _prepare_df(self, data):
        df = pd.DataFrame(data)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values(by=['date'], inplace=True)

            if self._year:
                df = df[df['date'].dt.year == self._year]

        return df

    def _empty_list(self):
        arr = []
        for i in range(1, 13):
            month_len = calendar.monthlen(self._year, i)
            items = []
            for _ in range(0, month_len):
                items.append({'y': 0, 'gap': 0})
            arr.append(items)

        return arr
