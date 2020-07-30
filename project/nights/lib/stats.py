import calendar
from datetime import date
from typing import Dict, List

import pandas as pd
from django.db.models import QuerySet

from ...core.exceptions import MethodInvalid


class Stats():
    def __init__(self, year: int = None, data: List[Dict[date, float]] = None):
        self._year = year
        self._df = self._prepare_df(data if data else [])

    @staticmethod
    def months() -> List[str]:
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
    def weekdays() -> List[str]:
        return([
            'Pirmadienis',
            'Antradienis',
            'Trečiadienis',
            'Ketvirtadienis',
            'Penktadienis',
            'Šeštadienis',
            'Sekmadienis'
        ])

    def weekdays_stats(self) -> List[Dict[int, float]]:
        """Returns [{'weekday': int, 'count': float}]"""

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

    def months_stats(self) -> List[float]:
        """Returns  [float] * 12"""

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
        """
        If class called with year value method returns int

        else method returns {1999: 12, 2000: 15}
        """

        df = self._df.copy()

        if df.empty:
            return 0

        df = df.groupby(df['date'].dt.year)['qty'].sum()

        arr = df.to_dict()

        if self._year:
            return arr.get(self._year, 0)
        else:
            return arr


    def month_days(self):
        if not self._year:
            raise MethodInvalid('class Stats must be called with specified year.')

        arr = []
        for i in range(1, 13):
            month_len = calendar.monthlen(self._year, i)
            items = []
            for day in range(0, month_len):
                items.append(day + 1)
            arr.append(items)

        return arr

    def items(self):
        df = self._df.copy()

        if not df.empty:
            df = df.sort_values(by=['date'], ascending=False)

        return df.to_dict('records')

    def _prepare_df(self, data):
        if isinstance(data, QuerySet):
            data = data.values()

        df = pd.DataFrame(data)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values(by=['date'], inplace=True)

            if self._year:
                df = df[df['date'].dt.year == self._year]

            # copy column quantity to qty
            if 'quantity' in df:
                df['qty'] = df['quantity']

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
