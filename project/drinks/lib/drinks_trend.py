from dataclasses import dataclass
from datetime import date, timedelta
from functools import cached_property

from ...core.lib.date import ydays
from .drinks_options import DrinkConverter
from .drinks_stats import DataRow
from .drinks_year import YearBoundary


@dataclass(frozen=True)
class RecentPeriodComparison:
    current_period_average: float  # std av in the most recent window
    previous_period_average: float  # std av in the equal-length window right before it
    # magnitude of the change, 0.0 when there is no prior baseline
    percentage_change: float
    improving: bool
    has_data: bool = True


@dataclass(frozen=True)
class EmptyRecentPeriodComparison:
    current_period_average: float = 0.0
    previous_period_average: float = 0.0
    percentage_change: float = 0.0
    improving: bool = False
    has_data: bool = False


@dataclass(frozen=True)
class YearToDateComparison:
    current_year_average: float  # std av consumed year-to-date
    previous_year_average: float  # std av consumed to the same day-of-year last period
    percentage_change: float
    improving: bool
    has_past: bool = True


@dataclass(frozen=True)
class EmptyYearToDateComparison:
    current_year_average: float
    previous_year_average: float = 0.0
    percentage_change: float = 0.0
    improving: bool = False
    has_past: bool = False


@dataclass(frozen=True)
class YearEndProjection:
    # by year-end at the current pace, in the unit a yearly total is read in
    projected_total: float
    # allowed for the whole year, in that same unit
    target_total: float
    percentage_difference: float  # % over (+) or under (-) the yearly target
    over: bool
    has_target: bool = True


@dataclass(frozen=True)
class EmptyYearEndProjection:
    projected_total: float
    target_total: float = 0.0
    percentage_difference: float = 0.0
    over: bool = False
    has_target: bool = False


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

        self._current_year_records = current_daily or []
        self._past_year_records = past_daily or []
        self._year = YearBoundary.from_records(self._current_year_records, today)
        self.current_year = self._year.year

    @staticmethod
    def _date_range(start: date, end: date) -> list[date]:
        return [start + timedelta(days=i) for i in range((end - start).days + 1)]

    @staticmethod
    def _calculate_pct(current: float, past: float) -> float:
        if not past:
            return 0.0
        return round(abs(current - past) / past * 100, 1)

    @property
    def unit(self) -> str:
        return self._converter.display_unit

    @property
    def decimals(self) -> int:
        return self._converter.display_decimals

    @cached_property
    def daily_volume(self) -> list[float]:
        """Dense day-by-day amount in the unit it is shown in (0 on days
        without records)."""
        by_date = {row.date: row.stdav for row in self._current_year_records}
        start = date(self.current_year, 1, 1)

        return [
            self._converter.stdav_to_display(by_date.get(day, 0.0))
            for day in self._date_range(start, self._year.end_date)
        ]

    @cached_property
    def date_labels(self) -> list[str]:
        start = date(self.current_year, 1, 1)
        return [day.isoformat() for day in self._date_range(start, self._year.end_date)]

    @cached_property
    def cumulative_categories(self) -> list[str]:
        start = date(self.current_year, 1, 1)
        end = date(self.current_year, 12, 31)
        return [day.isoformat() for day in self._date_range(start, end)]

    @property
    def total_unit(self) -> str:
        return self._converter.total_unit

    def _running_total(self, rows: list[DataRow], days: int) -> list[float]:
        """Day-by-day running total in ``total_unit``."""
        by_yday = {row.date.timetuple().tm_yday: row.stdav for row in rows}
        cum = 0.0
        series = []
        for i in range(1, days + 1):
            cum += self._converter.stdav_to_total(by_yday.get(i, 0.0))
            series.append(cum)
        return series

    @cached_property
    def cumulative_current_year(self) -> list[float]:
        return self._running_total(self._current_year_records, self._year.days_elapsed)

    @cached_property
    def cumulative_past_year(self) -> list[float]:
        return self._running_total(self._past_year_records, ydays(self.current_year))

    @cached_property
    def cumulative_target(self) -> list[float]:
        days = ydays(self.current_year)
        if not self._target:
            return [0.0] * days

        # the target is already a daily amount in the shown unit, so the pace is
        # just that amount accumulated — only the total scale still applies
        pace = self._converter.display_to_total(self._target)
        return [pace * i for i in range(1, days + 1)]

    def calculate_rolling_average(self, window: int) -> list[float]:
        """Trailing mean per day in ``unit``, aligned to ``date_labels``.

        The window is seeded with the ``window - 1`` days before Jan 1 (pulled
        from the previous year) and always divided by the full window, so the
        line doesn't spike at the year start when only a day or two would
        otherwise be available to average.
        """
        lookup = self._stdav_by_date
        start = date(self.current_year, 1, 1) - timedelta(days=window - 1)

        series = [
            self._converter.stdav_to_display(lookup.get(day, 0.0))
            for day in self._date_range(start, self._year.end_date)
        ]

        return [
            sum(series[i - window + 1 : i + 1]) / window
            for i in range(window - 1, len(series))
        ]

    def compare_recent_period(
        self, days: int
    ) -> RecentPeriodComparison | EmptyRecentPeriodComparison:
        """Most recent ``days`` vs the equal-length window right before it."""
        end = self._year.end_date
        current_start = end - timedelta(days=days)
        previous_start = end - timedelta(days=2 * days)
        lookup = self._stdav_by_date

        recent_avg = sum(v for d, v in lookup.items() if current_start < d <= end)
        previous_avg = sum(
            v for d, v in lookup.items() if previous_start < d <= current_start
        )

        if not recent_avg and not previous_avg:
            return EmptyRecentPeriodComparison()

        return RecentPeriodComparison(
            round(recent_avg, 1),
            round(previous_avg, 1),
            self._calculate_pct(recent_avg, previous_avg),
            improving=recent_avg < previous_avg,
        )

    def compare_year_to_date(self) -> YearToDateComparison | EmptyYearToDateComparison:
        day_of_year = self._year.days_elapsed
        current = self._sum_stdav(self._current_year_records, day_of_year)

        if not self._past_year_records:
            return EmptyYearToDateComparison(current)

        past = self._sum_stdav(self._past_year_records, day_of_year)

        return YearToDateComparison(
            current,
            past,
            self._calculate_pct(current, past),
            improving=current < past,
        )

    def calculate_projection(self) -> YearEndProjection | EmptyYearEndProjection:
        # the pace and the Drink Target must be measured the same way: the target
        # is a daily amount in the shown unit, so the pace is taken there too and
        # only then scaled to a yearly total
        days_passed = len(self.daily_volume)
        pace = sum(self.daily_volume) / days_passed if days_passed else 0.0
        days = ydays(self.current_year)

        projected = self._converter.display_to_total(pace * days)

        if not self._target:
            return EmptyYearEndProjection(round(projected, 1))

        allowed = self._converter.display_to_total(self._target * days)
        pct = 0.0
        if allowed:
            pct = round((projected - allowed) / allowed * 100, 1)

        return YearEndProjection(
            round(projected, 1),
            round(allowed, 1),
            pct,
            over=projected > allowed,
        )

    @cached_property
    def _stdav_by_date(self) -> dict:
        """Date -> std av across the current and previous year (for windows
        that straddle the year boundary)."""
        lookup = {row.date: row.stdav for row in self._past_year_records}
        lookup.update({row.date: row.stdav for row in self._current_year_records})
        return lookup

    @staticmethod
    def _sum_stdav(rows: list[DataRow], day_of_year: int) -> float:
        return sum(
            row.stdav for row in rows if row.date.timetuple().tm_yday <= day_of_year
        )
