import calendar
import itertools as it
from datetime import date, datetime
from functools import cached_property, partial

import polars as pl
from polars.exceptions import ColumnNotFoundError

from ...core.exceptions import MethodInvalidError
from ...core.lib.translation import month_names, weekday_names


class Stats:
    def __init__(
        self,
        year: int | None = None,
        data: list[dict[date, float]] | None = None,
        past_latest: date | None = None,
    ):
        self._year = year
        self._past_latest = past_latest
        self._data = data
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
            return self._df.select(pl.col("qty").sum())[0, 0]
        except ColumnNotFoundError:
            return self._df.shape[0]

    def weekdays_stats(self) -> list[dict[int, float]]:
        """Returns [{'weekday': int, 'count': float}]"""
        if self._full_year_df.is_empty():
            return [{"weekday": i, "count": 0} for i in range(7)]

        return (
            self._full_year_df.lazy()
            .group_by(weekday=pl.col("date").dt.weekday() - 1)
            .agg(count=pl.col("qty").sum())
            .sort("weekday")
            .collect()
            .to_dicts()
        )

    def months_stats(self) -> list[float]:
        """Returns [float] * 12"""
        if self._full_year_df.is_empty():
            return [0.0] * 12

        return (
            self._full_year_df.lazy()
            .group_by(month=pl.col("date").dt.month())
            .agg(qty=pl.col("qty").sum())
            .sort("month")
            .collect()["qty"]
            .to_list()
        )

    def year_totals(self) -> int | dict[int, float]:
        """
        If class called with year value method returns int
        else method returns {1999: 12, 2000: 15}
        """
        if self._df.is_empty():
            return 0 if self._year else {}

        summary_df = (
            self._df.lazy()
            .group_by(year=pl.col("date").dt.year())
            .agg(qty=pl.col("qty").sum())
            .sort("year")
            .collect()
        )

        if self._year:
            return summary_df.to_dicts()[0].get("qty", 0)

        return {row["year"]: row["qty"] for row in summary_df.to_dicts()}

    def gaps(self) -> dict[int, int]:
        """Returns dictionary(int: int) = {gap: count}"""
        history_df = self._calculate_gaps()

        if history_df.is_empty():
            return {}

        summary_df = (
            history_df.lazy()
            .group_by("duration")
            .agg(qty=pl.col("qty").count())
            .sort("duration")
            .collect()
        )
        return {row["duration"]: row["qty"] for row in summary_df.to_dicts()}

    @cached_property
    def _df(self) -> pl.DataFrame:
        return self._prepare_data_frame(self._data)

    @cached_property
    def _full_year_df(self) -> pl.DataFrame:
        if self._df.is_empty():
            return self._df

        first_date = date(self._df[0, "date"].year, 1, 1)
        last_date = date(self._df[-1, "date"].year, 12, 31)

        date_range = pl.date_range(first_date, last_date, "1d", eager=True).alias(
            "date"
        )
        empty_df = pl.DataFrame({"date": date_range})

        return empty_df.join(self._df, on="date", how="left").fill_null(0)

    def _prepare_data_frame(self, data) -> pl.DataFrame:
        """Initial data preparation and cleaning"""
        data = data if isinstance(data, list) else list(data)
        history_df = pl.DataFrame(data or [])

        if history_df.is_empty():
            return history_df

        if "quantity" in history_df.columns:
            history_df = history_df.rename({"quantity": "qty"})

        if self._year:
            history_df = history_df.filter(pl.col("date").dt.year() == self._year)

        return history_df.sort("date")

    def _calculate_gaps(self) -> pl.DataFrame:
        if self._df.is_empty():
            return self._df

        first_record_date = self._df[0, "date"]
        past_record_date = self._past_latest or date(first_record_date.year, 1, 1)
        first_gap_days = (first_record_date - past_record_date).days

        return (
            self._df.lazy()
            .with_columns(
                duration=pl.col("date").diff().dt.total_days().fill_null(first_gap_days)
            )
            .sort("date")
            .collect()
        )


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
