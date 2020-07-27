import calendar

import pandas as pd


class Stats():
    def __init__(self, data):
        self._df = self._prepare_df(data)

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

    def year_stats(self, year: int):
        arr = self._empty_list(year)
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

    def _prepare_df(self, data):
        df = pd.DataFrame(data)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])

        return df

    def _empty_list(self, year: int):
        arr = []
        for i in range(1, 13):
            month_len = calendar.monthlen(year, i)
            items = []
            for _ in range(0, month_len):
                items.append({'y': 0, 'gap': 0})
            arr.append(items)

        return arr
