import calendar
import contextlib
import itertools as it
from datetime import date, datetime

import pandas as pd
from django.db import models
from django.db.models import QuerySet

from ...core.exceptions import MethodInvalid
from ...core.lib.translation import month_names, weekday_names


class Stats:
    _cdf: None

    def __init__(self,
                 year: int = None,
                 data: list[dict[date, float]] = None,
                 past_latest: date = None):

        self._year = year
        self._past_latest = past_latest
        self._df = self._prepare_df(data)

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

        data = {'weekday': range(7), 'qty': [0]*7}
        empty_df = pd.DataFrame(data=data).set_index('weekday')

        if self._df.empty:
            df = empty_df
        else:
            df = self._df.copy()
            df['weekday'] = df['date'].dt.dayofweek
            df = df.groupby('weekday')['qty'].sum().to_frame()
            df = empty_df.add(df, fill_value=0)

        df.reset_index(inplace=True)
        df.rename(columns = {'qty':'count'}, inplace = True)

        return df.to_dict('records')

    def months_stats(self) -> list[float]:
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

    def chart_calendar(self) -> list[dict]:
        if not self._year:
            raise MethodInvalid('class Stats must be called with specified year.')

        # _cdf variable will be used in _day_info method
        self._cdf = self._make_calendar_dataframe()

        def func(m: int):
            return it.product(
                [self._year], [m], calendar.Calendar(0).itermonthdays2(self._year, m))

        arr = map(func, range(1, 13))
        data = map(self._day_info, it.chain(*arr), it.count(0))
        months = self.months()

        # groupby year-month e.g. 1999-01
        return [{
            'name': months[int(key[6:]) - 1],
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
        """
        returns dictionary(int: int) = {gap: count}
        """
        df = self._df.copy()

        if df.empty:
            return {}

        df = self._calc_gaps(df)

        return df['duration'].value_counts().sort_index().to_dict()

    def _prepare_df(self, data):
        """
        some methods from QuerySet managers, e.g. sum_by_day returns <Queryset[dict(),]>
        other methods e.g. year, items returns <QuerySet[models.Model instance,]
        QuerySet with model instances need to convert to list[dict]
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

    def _day_info(self, data: tuple[int, int, tuple[int, int]], i: int) -> list:
        (year, month, (day, weekday)) = data
        x, y = divmod(i, 7)

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

        # self._cdf dataframe is made in self._make_calandar_dataframe()
        if dt in self._cdf.index:
            # .loc returns pd.serries -> stdav, qty, duration
            flt = self._cdf.loc[dt]
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

    def _make_calendar_dataframe(self):
        df = self._df.copy()

        if not df.empty:
            df = self._calc_gaps(df)
            df['date'] = pd.to_datetime(df.date).dt.date
            df.set_index('date', inplace=True)

        return df
