from dataclasses import dataclass
from datetime import date, timedelta
from functools import cached_property

from ...core.lib.date import ydays
from .drinks_options import DrinkConverter
from .drinks_stats import DataRow


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
    # projected volume by year-end at the current pace, litres
    projected_volume_liters: float
    # allowed volume for the whole year, litres
    target_volume_liters: float
    percentage_difference: float  # % over (+) or under (-) the yearly target
    over: bool
    has_target: bool = True


@dataclass(frozen=True)
class EmptyYearEndProjection:
    projected_volume_liters: float
    target_volume_liters: float = 0.0
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
        self._today = today or date.today()

        self._current_year_records = current_daily or []
        self._past_year_records = past_daily or []
        self.current_year = (
            self._current_year_records[0].date.year
            if self._current_year_records
            else self._today.year
        )

    @cached_property
    def _year_end_date(self) -> date:
        if self.current_year == self._today.year:
            return self._today
        return date(self.current_year, 12, 31)

    @staticmethod
    def _date_range(start: date, end: date) -> list[date]:
        return [start + timedelta(days=i) for i in range((end - start).days + 1)]

    @staticmethod
    def _calculate_pct(current: float, past: float) -> float:
        if not past:
            return 0.0
        return round(abs(current - past) / past * 100, 1)

    @cached_property
    def daily_volume_ml(self) -> list[float]:
        """Dense day-by-day volume in ml (0 on days without records)."""
        by_date = {row.date: row.stdav for row in self._current_year_records}
        start = date(self.current_year, 1, 1)

        return [
            self._converter.stdav_to_ml(by_date.get(day, 0.0))
            for day in self._date_range(start, self._year_end_date)
        ]

    @cached_property
    def date_labels(self) -> list[str]:
        start = date(self.current_year, 1, 1)
        return [day.isoformat() for day in self._date_range(start, self._year_end_date)]

    @cached_property
    def cumulative_categories(self) -> list[str]:
        start = date(self.current_year, 1, 1)
        end = date(self.current_year, 12, 31)
        return [day.strftime("%m-%d") for day in self._date_range(start, end)]

    @cached_property
    def cumulative_current_year_ml(self) -> list[float]:
        by_yday = {
            row.date.timetuple().tm_yday: row.stdav
            for row in self._current_year_records
        }
        days_passed = self._year_end_date.timetuple().tm_yday
        cum = 0.0
        series = []
        for i in range(1, days_passed + 1):
            cum += self._converter.stdav_to_ml(by_yday.get(i, 0.0))
            series.append(cum)
        return series

    @cached_property
    def cumulative_past_year_ml(self) -> list[float]:
        from ...core.lib.date import ydays

        by_yday = {
            row.date.timetuple().tm_yday: row.stdav for row in self._past_year_records
        }
        days = ydays(self.current_year)
        cum = 0.0
        series = []
        for i in range(1, days + 1):
            cum += self._converter.stdav_to_ml(by_yday.get(i, 0.0))
            series.append(cum)
        return series

    @cached_property
    def cumulative_target_ml(self) -> list[float]:
        from ...core.lib.date import ydays

        days = ydays(self.current_year)
        if not self._target:
            return [0.0] * days

        target_ml = self._target * days
        daily_pace = target_ml / days
        return [daily_pace * i for i in range(1, days + 1)]

    def calculate_rolling_average(self, window: int) -> list[float]:
        """Trailing mean in ml/day, aligned to ``date_labels``.

        The window is seeded with the ``window - 1`` days before Jan 1 (pulled
        from the previous year) and always divided by the full window, so the
        line doesn't spike at the year start when only a day or two would
        otherwise be available to average.
        """
        lookup = self._stdav_by_date
        start = date(self.current_year, 1, 1) - timedelta(days=window - 1)

        series = [
            self._converter.stdav_to_ml(lookup.get(day, 0.0))
            for day in self._date_range(start, self._year_end_date)
        ]

        return [
            sum(series[i - window + 1 : i + 1]) / window
            for i in range(window - 1, len(series))
        ]

    def compare_recent_period(
        self, days: int
    ) -> RecentPeriodComparison | EmptyRecentPeriodComparison:
        """Most recent ``days`` vs the equal-length window right before it."""
        end = self._year_end_date
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
        day_of_year = self._year_end_date.timetuple().tm_yday
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
        days_passed = len(self.daily_volume_ml)
        pace = sum(self.daily_volume_ml) / days_passed if days_passed else 0.0  # ml/day
        projected_ml = pace * ydays(self.current_year)
        projected_l = round(projected_ml / 1000, 1)

        if not self._target:
            return EmptyYearEndProjection(projected_l)

        target_ml = self._target * ydays(self.current_year)
        pct = 0.0
        if target_ml:
            pct = round((projected_ml - target_ml) / target_ml * 100, 1)

        return YearEndProjection(
            projected_l,
            round(target_ml / 1000, 1),
            pct,
            over=projected_ml > target_ml,
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
