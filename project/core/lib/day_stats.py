from datetime import date, datetime
from functools import cached_property

import polars as pl
from polars.exceptions import ColumnNotFoundError

from .translation import month_names, weekday_names


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

    def weekdays_stats(self) -> list[dict[str, float]]:
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

    def year_total(self) -> float:
        if self._df.is_empty():
            return 0.0

        return self._totals_by_year_df().to_dicts()[0].get("qty", 0.0)

    def totals_by_year(self) -> dict[int, float]:
        if self._df.is_empty():
            return {}

        return {row["year"]: row["qty"] for row in self._totals_by_year_df().to_dicts()}

    def gaps(self) -> dict[int, int]:
        """{gap in days: how many gaps of that length}"""
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

    def _totals_by_year_df(self) -> pl.DataFrame:
        return (
            self._df.lazy()
            .group_by(year=pl.col("date").dt.year())
            .agg(qty=pl.col("qty").sum())
            .sort("year")
            .collect()
        )

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
