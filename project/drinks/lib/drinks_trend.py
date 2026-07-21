from dataclasses import dataclass
from datetime import date, timedelta
from functools import cached_property

from ...core.lib.date import ydays
from .drinks_options import DrinkConverter
from .drinks_stats import DataRow


@dataclass(frozen=True)
class PeriodStats:
    current: float  # std av in the most recent window
    past: float  # std av in the equal-length window right before it
    pct: float | None  # magnitude of the change, None when there is no prior baseline
    improving: bool
    has_data: bool


@dataclass(frozen=True)
class YtdStats:
    current: float  # std av consumed year-to-date
    past: float  # std av consumed to the same day-of-year last period
    pct: float | None
    improving: bool
    has_past: bool


@dataclass(frozen=True)
class ProjectionStats:
    projected_l: float  # projected volume by year-end at the current pace, litres
    target_l: float  # allowed volume for the whole year, litres
    pct: float | None  # % over (+) or under (-) the yearly target
    over: bool
    has_target: bool


class TrendStats:
    """Behaviour-change metrics derived from the daily (date, stdav) series."""

    def __init__(
        self,
        converter: DrinkConverter,
        current_daily: list[DataRow] | None = None,
        past_daily: list[DataRow] | None = None,
        target: float = 0.0,
        today: date | None = None,
    ):
        self._converter = converter
        self._target = target
        self._today = today or date.today()

        self._current = current_daily or []
        self._past = past_daily or []
        self.year = self._current[0].date.year if self._current else self._today.year

    @cached_property
    def _end_date(self) -> date:
        if self.year == self._today.year:
            return self._today
        return date(self.year, 12, 31)

    @staticmethod
    def _date_range(start: date, end: date) -> list[date]:
        return [start + timedelta(days=i) for i in range((end - start).days + 1)]

    @staticmethod
    def _calculate_pct(current: float, past: float) -> float | None:
        return round(abs(current - past) / past * 100, 1) if past else None

    @cached_property
    def daily_ml(self) -> list[float]:
        """Dense day-by-day volume in ml (0 on days without records)."""
        by_date = {row.date: row.stdav for row in self._current}
        start = date(self.year, 1, 1)

        return [
            self._converter.stdav_to_ml(by_date.get(day, 0.0))
            for day in self._date_range(start, self._end_date)
        ]

    @cached_property
    def categories(self) -> list[str]:
        start = date(self.year, 1, 1)
        return [day.isoformat() for day in self._date_range(start, self._end_date)]

    def rolling(self, window: int) -> list[float]:
        """Trailing mean in ml/day, aligned to ``categories``.

        The window is seeded with the ``window - 1`` days before Jan 1 (pulled
        from the previous year) and always divided by the full window, so the
        line doesn't spike at the year start when only a day or two would
        otherwise be available to average.
        """
        lookup = self._combined_stdav
        start = date(self.year, 1, 1) - timedelta(days=window - 1)

        series = [
            self._converter.stdav_to_ml(lookup.get(day, 0.0))
            for day in self._date_range(start, self._end_date)
        ]

        return [
            sum(series[i - window + 1 : i + 1]) / window
            for i in range(window - 1, len(series))
        ]

    def period(self, days: int) -> PeriodStats:
        """Most recent ``days`` vs the equal-length window right before it."""
        end = self._end_date
        current_start = end - timedelta(days=days)
        previous_start = end - timedelta(days=2 * days)
        lookup = self._combined_stdav

        current = sum(v for d, v in lookup.items() if current_start < d <= end)
        past = sum(v for d, v in lookup.items() if previous_start < d <= current_start)

        if not current and not past:
            return PeriodStats(0.0, 0.0, None, improving=False, has_data=False)

        return PeriodStats(
            round(current, 1),
            round(past, 1),
            self._calculate_pct(current, past),
            improving=current < past,
            has_data=True,
        )

    def ytd(self) -> YtdStats:
        day_of_year = self._end_date.timetuple().tm_yday
        current = self._sum_stdav(self._current, day_of_year)

        if not self._past:
            return YtdStats(current, 0.0, None, improving=False, has_past=False)

        past = self._sum_stdav(self._past, day_of_year)

        return YtdStats(
            current,
            past,
            self._calculate_pct(current, past),
            improving=current < past,
            has_past=True,
        )

    def projection(self) -> ProjectionStats:
        days_passed = len(self.daily_ml)
        pace = sum(self.daily_ml) / days_passed if days_passed else 0.0  # ml/day
        projected_ml = pace * ydays(self.year)
        projected_l = round(projected_ml / 1000, 1)

        if not self._target:
            return ProjectionStats(projected_l, 0.0, None, over=False, has_target=False)

        target_ml = self._target * ydays(self.year)
        pct = (
            round((projected_ml - target_ml) / target_ml * 100, 1)
            if target_ml
            else None
        )

        return ProjectionStats(
            projected_l,
            round(target_ml / 1000, 1),
            pct,
            over=projected_ml > target_ml,
            has_target=True,
        )

    @cached_property
    def _combined_stdav(self) -> dict:
        """Date -> std av across the current and previous year (for windows
        that straddle the year boundary)."""
        lookup = {row.date: row.stdav for row in self._past}
        lookup.update({row.date: row.stdav for row in self._current})
        return lookup

    @staticmethod
    def _sum_stdav(rows: list[DataRow], day_of_year: int) -> float:
        return sum(
            row.stdav for row in rows if row.date.timetuple().tm_yday <= day_of_year
        )
