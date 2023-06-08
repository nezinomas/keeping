import calendar
import functools
import itertools as it
from datetime import date, datetime

import polars as pl
from polars import DataFrame as DF

from ...core.exceptions import MethodInvalid
from ...core.lib.translation import month_names, weekday_names


class Stats:
    def __init__(
        self,
        year: int = None,
        data: list[dict[date, float]] = None,
        past_latest: date = None,
    ):
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
        try:
            return self._df.select(pl.col("qty").sum())[0,0]
        except pl.ColumnNotFoundError:
            return self._df.shape[0]

    def weekdays_stats(self) -> list[dict[int, float]]:
        """Returns [{'weekday': int, 'count': float}]"""
        if self._df.is_empty():
            return [{"weekday": i, "count": 0} for i in range(7)]

        df = (
            self._insert_empty_rows(self._df)
            .lazy()
            .fill_null(0)
            .groupby(pl.col("date").dt.weekday() - 1)
            .agg(pl.col("qty").sum())
            .rename({"date": "weekday", "qty": "count"})
            .sort("weekday")
            .collect()
        )
        return df.to_dicts()

    def months_stats(self) -> list[float]:
        """Returns  [float] * 12"""
        if self._df.is_empty():
            return [0.0] * 12

        df = (
            self._insert_empty_rows(self._df)
            .lazy()
            .fill_null(0)
            .groupby(pl.col("date").dt.month())
            .agg(pl.col("qty").sum())
            .sort("date")
            .collect()
        )
        return df["qty"].to_list()

    def chart_calendar(self) -> list[dict]:
        if not self._year:
            raise MethodInvalid("class Stats must be called with specified year.")

        def func(month: int):
            return it.product(
                [self._year],
                [month],
                calendar.Calendar(0).itermonthdays2(self._year, month),
            )

        # make calendar_df with calculated gaps and pass it to _day_info method
        calendar_df = self._calc_gaps()
        day_info = functools.partial(self._day_info, calendar_df=calendar_df)

        arr = map(func, range(1, 13))
        data = map(day_info, it.chain(*arr), it.count(0))
        # month names list
        names = self.months()

        # groupby year-month e.g. 1999-01
        return [
            {
                "name": names[int(key[5:]) - 1],
                "keys": ["x", "y", "value", "week", "date", "qty", "gap"],
                "data": list(group),
            }
            for key, group in it.groupby(data, lambda x: x[4][:7])
        ]

    def year_totals(self):
        """
        If class called with year value method returns int

        else method returns {1999: 12, 2000: 15}
        """
        if self._df.is_empty():
            return 0 if self._year else {}

        df = (
            self._df
            .lazy()
            .groupby(pl.col("date").dt.year())
            .agg(pl.col("qty").sum())
            .sort("date")
            .collect()
        )

        if self._year:
            return df.to_dicts()[0].get("qty", 0)

        return {row["date"]: row["qty"] for row in df.to_dicts()}

    def gaps(self) -> dict[int, int]:
        """Returns dictionary(int: int) = {gap: count}"""
        # calculate gaps
        df = self._calc_gaps()

        if df.is_empty():
            return {}

        df = (
            df
            .lazy()
            .groupby("duration")
            .agg(pl.col("qty").count())
            .sort("duration")
            .collect()
        )
        return {x["duration"]: x["qty"] for x in df.to_dicts()}

    def _make_dataframe(self, data):
        """Make DataFrame"""
        data = data if isinstance(data, list) else list(data)
        df = pl.DataFrame(data or [])

        if df.is_empty():
            return df

        def filter_by_year(df: DF) -> pl.Expr:
            return (
                df.filter(pl.col("date").dt.year() == self._year) if self._year else df
            )

        def copy_quantity(df: DF) -> pl.Expr:
            return df.rename({"quantity": "qty"}) if "quantity" in df.columns else df

        return df.sort("date").pipe(filter_by_year).pipe(copy_quantity)

    def _insert_empty_rows(self, df: DF) -> DF:
        first_date = date(df.head(1)[0, "date"].year, 1, 1)
        last_date = date(df.tail(1)[0, "date"].year, 12, 31)
        date_range = pl.date_range(first_date, last_date, "1d", eager=True)
        df_empty = pl.DataFrame({"date": date_range, "qty": [0.0] * len(date_range)})
        return pl.concat([df, df_empty], how="vertical")

    def _calc_gaps(self) -> pl.DataFrame:
        if self._df.is_empty():
            return self._df

        def first_gap(df: DF) -> pl.Expr:
            first_record_date = df[0, "date"]
            past_record_date = self._past_latest or date(first_record_date.year, 1, 1)
            df[0, "duration"] = (first_record_date - past_record_date).days
            return df

        return (
            self._df
            .lazy()
            .with_columns((pl.col("date").diff().dt.days()).alias("duration"))
            .fill_null(0)
            .sort("date")
            .collect()
            .pipe(first_gap)
        )

    def _day_info(self, data: tuple, iteration: int, calendar_df: DF) -> list:
        (year, month, (day, weekday)) = data
        x, y = divmod(iteration, 7)
        dt = date(year, month, day) if day else None
        # if day is 0 then day = last month day
        day = day or calendar.monthrange(year, month)[1]
        weeknumber = date(year, month, day).isocalendar()[1]
        color = self._cell_color(dt, weekday)
        str_date = str(dt) if dt else f'{year}-{str(month).rjust(2, "0")}'

        # calendar_df dataframe is made in self._make_calandar_dataframe()
        qty_and_duration = []
        if not calendar_df.is_empty() and dt in calendar_df["date"]:
            flt = calendar_df.filter(pl.col("date") == dt).row(0, named=True)
            color = flt["qty"]  # color depends on qty
            qty_and_duration = [flt["qty"], flt["duration"]]

        return [
            x + month - 1,  # adjust x value for empty col between months
            y,
            color,
            weeknumber,
            str_date,
            *qty_and_duration,
        ]

    def _cell_color(self, dt: date, weekday: int) -> float:
        # colors for 5(saturday) -> #dfdfdf 6(sunday) -> #c3c4c2
        # other days 0-5 -> #f4f4f4
        # float convert to color code in chart_calendar.js
        if not dt:
            return 0

        # current day -> #c9edff
        if dt == self._now_date:
            return 0.0005  # highlight current day

        return (0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0002, 0.0003)[weekday]
