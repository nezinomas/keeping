import calendar
import contextlib
from datetime import date, datetime
from typing import Dict, List

import pandas as pd
from django.db import models
from django.db.models import QuerySet

from ...core.exceptions import MethodInvalid
from ...core.lib.translation import month_names, weekday_names


class Stats():
    def __init__(self,
                 year: int = None,
                 data: List[Dict[date, float]] = None,
                 past_latest: date = None):

        self._year = year
        self.past_latest = past_latest
        self._df = self._prepare_df(data)

    @staticmethod
    def months() -> List[str]:
        return list(month_names().values())

    @staticmethod
    def weekdays() -> List[str]:
        return list(weekday_names().values())

    @property
    def number_of_recods(self):
        return self._df.shape[0]

    def weekdays_stats(self) -> List[Dict[int, float]]:
        """Returns [{'weekday': int, 'count': float}]"""

        df = self._df.copy()

        if not df.empty:
            df['weekday'] = df['date'].dt.dayofweek

            df = df.groupby('weekday')['qty'].sum()

        df = df.to_dict()  # {0: 1, 1: 0} == {weekday: counts, }

        # return list with zeros
        arr = [{'weekday': i, 'count': 0} for i in range(7)]

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

        arr = [0] * 12  # return list filled with zeros

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

        df = self._calc_gaps(df)

        # copy values from DataFrame to arr
        for _, row in df.iterrows():
            month = row['date'].month
            day = row['date'].day

            arr[month - 1][day - 1]['y'] = row['qty']
            arr[month - 1][day - 1]['gap'] = row['duration']

        return arr

    def chart_calendar(self):
        if not self._year:
            raise MethodInvalid('class Stats must be called with specified year.')

        df = self._df.copy()

        if not df.empty:
            df = self._calc_gaps(df)
            df['date'] = pd.to_datetime(df.date).dt.date
            df.set_index('date', inplace=True)

        x = 0
        y = -1
        week = 1
        items = []
        _calendar = calendar.Calendar(0)

        for month in range(1, 13):
            data = []
            monthdays = _calendar.itermonthdays(year=self._year, month=month)
            for day in monthdays:
                val = 0
                dt = None
                qty = None

                if y >= 6:
                    y = 0
                    x += 1
                else:
                    y += 1

                with contextlib.suppress(ValueError):
                    dt = date(self._year, month, day)
                row = []
                if dt:
                    # set values for saturday and sunday
                    week = dt.isocalendar()[1]
                    weekday = dt.weekday()

                    if weekday == 5:
                        val = 0.02  # saturday value for chart
                    elif weekday == 6:
                        val = 0.03  # sunday
                    else:
                        val = 0.01  # monday-friday

                    # current day
                    if dt == datetime.now().date():
                        val = 0.05  # highlight current day

                    # get gap and duration
                    with contextlib.suppress(KeyError):
                        _f = df.loc[dt]
                        qty = val = _f.qty
                        row = [qty, _f.duration]
                data.append([x, y, val, week, str(dt), *row])

            x += 1

            items.append({
                'name': self.months()[month-1],
                'keys': ['x', 'y', 'value', 'week', 'date', 'qty', 'gap'],
                'data': data,
            })

        return items

    def year_totals(self):
        """
        If class called with year value method returns int

        else method returns {1999: 12, 2000: 15}
        """

        df = self._df.copy()

        if 'qty' in df:
            df = df.groupby(df['date'].dt.year)['qty'].sum()

        arr = df.to_dict()

        return arr.get(self._year, 0) if self._year else arr

    def month_days(self):
        if not self._year:
            raise MethodInvalid('class Stats must be called with specified year.')

        arr = []
        for i in range(1, 13):
            month_len = calendar.monthrange(self._year, i)[1]
            arr.append([day + 1 for day in range(month_len)])

        return arr

    def items(self):
        df = self._df.copy()

        if not df.empty:
            df = df.sort_values(by=['date'], ascending=False)

        return df.to_dict('records')

    def gaps(self) -> Dict[int, int]:
        """
        returns dictionary(int: int) = {gap: count}
        """
        df = self._df.copy()

        if df.empty:
            return {}

        df = self._calc_gaps(df)

        return df['duration'].value_counts().sort_index().to_dict()

    def current_gap(self):
        if not self._year:
            raise MethodInvalid('class Stats must be called with specified year.')

        if self._df.empty:
            return

        if datetime.now().year != self._year:
            return

        return (datetime.now() - self._df['date'].iloc[-1]).days

    def _prepare_df(self, data):
        """
        some methods from QuerySet managers, e.g. sum_by_day returns <Queryset[dict(),]>
        other methods e.g. year, items returns <QuerySet[models.Model instance,]
        QuerySet with model instances need to convert to List[Dict]
        """

        if isinstance(data, QuerySet):
            first = None

            with contextlib.suppress(IndexError):
                first = data[0]

            if first and isinstance(first, models.Model):
                data = data.values()

        df = pd.DataFrame(data or [])

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
            month_len = calendar.monthrange(self._year, i)[1]
            arr.append([{'y': 0, 'gap': 0} for _ in range(month_len)])

        return arr

    def _calc_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        # time gap between days with records
        df['duration'] = df['date'].diff().dt.days
        first_record_date = df['date'].iloc[0]

        if self.past_latest:
            first_date = pd.to_datetime(self.past_latest)
        else:
            first_date = pd.to_datetime(f'{first_record_date.year}-01-01')

        # repair time gap for first year record
        first_duration = (first_record_date - first_date).days
        df.loc[df.index[0], 'duration'] = first_duration

        df['duration'] = df['duration'].astype(int)

        return df
