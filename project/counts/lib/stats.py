import calendar
import contextlib
import functools
import itertools as it
from datetime import date, datetime

import pandas as pd
from django.db import models
from django.db.models import QuerySet
from pandas import DataFrame as DF

from ...core.exceptions import MethodInvalid
from ...core.lib.translation import month_names, weekday_names


class Stats:
    def __init__(self,
                 year: int = None,
                 data: list[dict[date, float]] = None,
                 past_latest: date = None):

        self._year = year
        self._past_latest = past_latest
        self._df = self._make_dataframe(data)

        self._now_date = datetime.now().date()

    @staticmethod
    def months() -> list[str]:
        return list(month_names().values())

    @staticmethod
    def weekdays() -> list[str]:
        return list(weekday_names().values())

    @property
    def number_of_records(self):
        return self._df.shape[0]

    def weekdays_stats(self) -> list[dict[int, float]]:
        """Returns [{'weekday': int, 'count': float}]"""
        if self._df.empty:
            return [{'weekday': i, 'count': 0} for i in range(7)]
        # groupby weekday and sum qty
        df = self._df.groupby(self._df['date'].dt.dayofweek)['qty'].sum()
        # insert missing rows if any
        df = df.reindex(range(7), fill_value=0)
        # rename columns
        df = df.reset_index().rename(columns={'date': 'weekday', 'qty': 'count'})
        return df.to_dict('records')

    def months_stats(self) -> list[float]:
        """Returns  [float] * 12"""
        if self._df.empty:
            return [0.0] * 12
        # group by month and sum qty
        df = self._df.groupby(self._df['date'].dt.month)['qty'].sum()
        # insert missing rows if any
        df = df.reindex(range(1,13), fill_value=0)
        return df.to_list()

    def chart_calendar(self) -> list[dict]:
        if not self._year:
            raise MethodInvalid('class Stats must be called with specified year.')

        def func(m: int):
            return it.product(
                [self._year], [m], calendar.Calendar(0).itermonthdays2(self._year, m))

        # make calendar_df with calculated gaps and pass it to _day_info method
        calendar_df = self._make_calendar_dataframe()
        day_info = functools.partial(self._day_info, calendar_df=calendar_df)

        arr = map(func, range(1, 13))
        data = map(day_info, it.chain(*arr), it.count(0))
        # month names list
        month_names = self.months()

        # groupby year-month e.g. 1999-01
        return [{
            'name': month_names[int(key[6:]) - 1],
            'keys': ['x', 'y', 'value', 'week', 'date', 'qty', 'gap'],
            'data': list(group),
        } for key, group in it.groupby(data, lambda x: x[4][:7])]

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

    def gaps(self) -> dict[int, int]:
        """ Returns dictionary(int: int) = {gap: count} """
        if self._df.empty:
            return {}
        # calculate gaps
        df = self._calc_gaps(self._df.copy())

        return df['duration'].value_counts().sort_index().to_dict()

    def _make_dataframe(self, data):
        """ Make DataFrame """
        df = pd.DataFrame(data or [])
        if df.empty:
            return df

        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(by=['date'], inplace=True)
        # if class initialzed with year, filter dataframe
        if self._year:
            df = df[df['date'].dt.year == self._year]
        # copy column quantity to qty
        if 'quantity' in df:
            df['qty'] = df['quantity']

        return df

    def _make_calendar_dataframe(self):
        if self._df.empty:
            return self._df
        # calculate gaps
        df = self._calc_gaps(self._df.copy())
        # convert 'date' column dtype from datetime to date
        df['date'] = pd.to_datetime(df.date).dt.date
        return df.set_index('date')

    def _calc_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        # time gap between days with records
        df['duration'] = df['date'].diff().dt.days
        first_record_date = df['date'].iloc[0]

        if self._past_latest:
            first_date = pd.to_datetime(self._past_latest)
        else:
            first_date = pd.to_datetime(f'{first_record_date.year}-01-01')

        # repair time gap for first year record
        first_duration = (first_record_date - first_date).days
        df.loc[df.index[0], 'duration'] = first_duration

        df['duration'] = df['duration'].astype(int)

        return df

    def _day_info(self, data: tuple, iteration: int, calendar_df: DF) -> list:
        (year, month, (day, weekday)) = data
        x, y = divmod(iteration, 7)

        dt = date(year, month, day) if day else None
        # if day == 0 then day = last month day
        day = day or calendar.monthrange(year, month)[1]

        arr = [
            x + month - 1,  # adjust x value for empty col between months
            y,
            self._cell_color(dt, weekday),  # color code
            date(year, month, day).isocalendar()[1],  # weeknumber
            str(dt) if dt else f'{year}-{str(month).rjust(2, "0")}',  # str(date)
        ]

        if not dt:
            return arr

        # calendar_df dataframe is made in self._make_calandar_dataframe()
        if dt in calendar_df.index:
            # .loc returns pd.serries -> stdav, qty, duration
            flt = calendar_df.loc[dt]
            arr[2] = flt.qty  # change color code
            arr.extend([flt.qty, flt.duration])

        return arr

    def _cell_color(self, dt: date, weekday: int) -> float:
        # colors for 5(saturday) -> #dfdfdf 6(sunday) -> #c3c4c2
        # other days 0-5 -> #f4f4f4
        # float convert to color code in chart_calendar.js
        if not dt:
            return 0.0

        # current day -> #c9edff
        if dt == self._now_date:
            return 0.05  # highlight current day

        return (0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03)[weekday]
