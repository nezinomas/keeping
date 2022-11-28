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
    def number_of_records(self):
        return self._df.shape[0]

    def weekdays_stats(self) -> List[Dict[int, float]]:
        """Returns [{'weekday': int, 'count': float}]"""

        df = self._df.copy()

        if not df.empty:
            df['weekday'] = df['date'].dt.dayofweek
            df = df.groupby('weekday')['qty'].sum()

        # {0: 1, 1: 0} == {weekday: counts, }; weekday[0] = monday
        df = df.to_dict()

        return [{'weekday': i, 'count': df.get(i) or 0} for i in range(7)]

    def months_stats(self) -> List[float]:
        """Returns  [float] * 12"""

        return_data = [0.0] * 12

        df = self._df.copy()
        if df.empty:
            return return_data

        # make YearMonth (e.g. 2000-01) column
        df.loc[:, 'YearMonth'] = df['date'].dt.to_period('M').astype(str)

        # group and sum by YearMonth
        df = df.groupby('YearMonth')['qty'].sum().to_frame()

        # make month digit column and make it as index
        df.loc[:, 'month'] = df.index.str[5:7].astype(int)
        df.set_index('month', inplace=True)

        # fill return_data array with counted qty from df
        for month, qty in df.qty.items():
            return_data[month - 1] = qty or 0.0

        return return_data

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

    def chart_calendar(self) -> list[dict]:
        if not self._year:
            raise MethodInvalid('class Stats must be called with specified year.')

        calendar_ = calendar.Calendar(0)
        df = self._make_calendar_dataframe(self._df)

        x = 0  # heatmap chart x coordinate
        y = -1  # heatmap chart y coordinate
        items = []
        for month in range(1, 13):
            data = []
            monthdays = calendar_.itermonthdays(year=self._year, month=month)
            for day in monthdays:
                if y == 6:
                    y = 0
                    x += 1
                else:
                    y += 1
                data.append([x, y, *self._day_info(self._year, month, day, df).values()])
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

    def _day_info(self, year: int, month: int, day: int, df: pd.DataFrame) -> dict:
        dt = date(year, month, day) if day else None
        row = {'color_value': 0, 'week': 1, 'date': str(dt)}

        if dt:
            # set values for saturday and sunday
            row['week'] = dt.isocalendar()[1]
            row['color_value'] = self._cell_color(dt)

            # get gap and duration
            with contextlib.suppress(KeyError):
                # .loc returns pd.serries -> stdav, qty, duration
                _f = df.loc[dt]
                row['color_value'] = row['qty'] = _f.qty
                row['gap'] = _f.duration

        return row

    def _cell_color(self, dt: date) -> float:
        # colors for 5(saturday) -> #dfdfdf 6(sunday) -> #c3c4c2
        # other days 0-5 -> #f4f4f4
        # float convert to color code in chart_calendar.js
        d = {5: 0.02, 6: 0.03}
        weekday = dt.weekday()
        val = d.get(weekday, 0.01)

        # current day -> #c9edff
        if dt == datetime.now().date():
            val = 0.05  # highlight current day

        return val

    def _make_calendar_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._df.copy()

        if not df.empty:
            df = self._calc_gaps(df)
            df['date'] = pd.to_datetime(df.date).dt.date
            df.set_index('date', inplace=True)

        return df
