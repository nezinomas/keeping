import calendar
import itertools as it
from datetime import date
from functools import partial

import polars as pl

from ...core.exceptions import MethodInvalidError
from ...core.lib.day_stats import Stats


class Calendar:
    def __init__(self, stats: Stats):
        self.stats = stats

    def chart_data(self) -> list[dict]:
        if not self.stats._year:
            raise MethodInvalidError(
                "Stats object must have a year for Calendar chart."
            )

        def month_generator(month: int):
            return it.product(
                [self.stats._year],
                [month],
                calendar.Calendar(0).itermonthdays2(self.stats._year, month),
            )

        calendar_df = self.stats._calculate_gaps()
        day_info_func = partial(self._day_info, calendar_df=calendar_df)

        month_range = map(month_generator, range(1, 13))
        processed_data = map(day_info_func, it.chain(*month_range), it.count(0))
        month_names_list = self.stats.months()

        return [
            {
                "name": month_names_list[int(month_key[5:]) - 1],
                "keys": ["x", "y", "value", "week", "date", "qty", "gap"],
                "data": list(group),
            }
            for month_key, group in it.groupby(processed_data, lambda x: x[4][:7])
        ]

    def _day_info(self, data: tuple, iteration: int, calendar_df: pl.DataFrame) -> list:
        (year, month, (day, weekday)) = data
        x, y = divmod(iteration, 7)
        dt = date(year, month, day) if day else None

        # if day is 0 then day = last month day
        day_for_week = day or calendar.monthrange(year, month)[1]
        weeknumber = date(year, month, day_for_week).isocalendar()[1]

        color = self._cell_color(dt, weekday)
        str_date = str(dt) if dt else f"{year}-{str(month).rjust(2, '0')}"

        qty_and_duration = []
        if not calendar_df.is_empty() and dt in calendar_df["date"].to_list():
            row_data = calendar_df.filter(pl.col("date") == dt).row(0, named=True)
            color = row_data["qty"]  # color depends on qty
            qty_and_duration = [row_data["qty"], row_data["duration"]]

        return [
            x + month - 1,  # adjust x value for empty col between months
            y,
            color,
            weeknumber,
            str_date,
            *qty_and_duration,
        ]

    def _cell_color(self, dt: date, weekday: int) -> float:
        if not dt:
            return 0

        if dt == self.stats._now_date:
            return 0.0005  # highlight current day

        # colors for weekdays
        return (0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0002, 0.0003)[weekday]
