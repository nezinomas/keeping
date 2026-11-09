from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from functools import cached_property

from ...core.lib.year_boundary import WEEKDAYS, YearBoundary
from .drinks_stats import (
    DataRow,
    EmptyYearOverYear,
    YearOverYear,
    YearOverYearReading,
)


@dataclass(frozen=True)
class ProfilePoint:
    """A run of calendar days, as both a frequency and a severity.

    The two are independent and a total answers neither: days can be drunk on
    rarely and heavily, or often and lightly, and only the pair distinguishes them.
    """

    calendar_days: int  # the days of the run the calendar has reached
    drinking_days: int
    stdav: float

    @property
    def drinking_day_share(self) -> float:
        return self.share_of(self.drinking_days)

    @property
    def intensity(self) -> float:
        return self.stdav / self.drinking_days if self.drinking_days else 0.0

    def share_of(self, days: int) -> float:
        return days / self.calendar_days if self.calendar_days else 0.0


@dataclass(frozen=True)
class WeekdayPoint(ProfilePoint):
    """One day of the week; its calendar days are how many the year has reached."""

    weekday: int  # 0 = Monday, matching date.weekday()


class FrequencyStats:
    """How often a user drinks, kept apart from how much on a day they do.

    Intensity stays in Std Av whatever the Drink type: no conversion in here."""

    def __init__(
        self,
        current_daily: Sequence[DataRow] = (),
        past_daily: Sequence[DataRow] = (),
        *,
        year: int,
        today: date,
    ):
        self._current_daily_records = current_daily
        self._past_daily_records = past_daily
        self._year = YearBoundary(year=year, today=today)
        self.current_year = self._year.year

    @property
    def is_current_year(self) -> bool:
        """Whether the year under view is still running, so that a share of it
        is a share of the days elapsed and not of all 365."""
        return self._year.is_current

    @property
    def days_elapsed(self) -> int:
        return self._year.days_elapsed

    @staticmethod
    def _count_drinking_days(records: Iterable[DataRow]) -> int:
        """Calendar days carrying a Drink, not rows: a day can hold several."""
        return len({row.date for row in records})

    def _point(self, records: Sequence[DataRow]) -> ProfilePoint:
        return ProfilePoint(
            calendar_days=self.days_elapsed,
            drinking_days=self._count_drinking_days(records),
            stdav=sum(row.stdav for row in records),
        )

    @cached_property
    def _year_point(self) -> ProfilePoint:
        return self._point(self._current_daily_records)

    @cached_property
    def _past_point(self) -> ProfilePoint:
        """Previous-year rows up to the same month and day as the year end: the
        same days a year back."""
        return self._point(self._year.clip(self._past_daily_records))

    @property
    def drinking_days(self) -> int:
        return self._year_point.drinking_days

    @cached_property
    def dry_days(self) -> int:
        """Days of the year reached with no Drink on them — so today for the
        year running, Dec 31 for one already over."""
        return max(self.days_elapsed - self.drinking_days, 0)

    @cached_property
    def drinking_day_share(self) -> float:
        return self._share(self.drinking_days)

    @cached_property
    def dry_share(self) -> float:
        return self._share(self.dry_days)

    def _share(self, days: int) -> float:
        """A count of days as a fraction of the year reached. A year with no
        Drinks scores 0.0: nobody logged it, which is not a year spent dry."""
        if not self._current_daily_records:
            return 0.0

        return self._year_point.share_of(days)

    @property
    def intensity(self) -> float:
        """Std Av per Drinking day — a year's total spread over the days it was
        actually drunk on, not over the days in the year."""
        return self._year_point.intensity

    def _compare(self, current: float, previous: float) -> YearOverYearReading:
        if not self._past_daily_records:
            return EmptyYearOverYear(current)

        return YearOverYear(current, previous)

    def compare_frequency(self) -> YearOverYearReading:
        return self._compare(self.drinking_days, self._past_point.drinking_days)

    def compare_intensity(self) -> YearOverYearReading:
        return self._compare(self.intensity, self._past_point.intensity)

    def weekday_profile(self) -> list[WeekdayPoint]:
        """Always seven points, Monday first: a weekday nobody drank on is a finding."""
        by_weekday: list[list[DataRow]] = [[] for _ in range(WEEKDAYS)]
        for row in self._current_daily_records:
            by_weekday[row.date.weekday()].append(row)

        return [
            self._weekday_point(weekday, rows)
            for weekday, rows in enumerate(by_weekday)
        ]

    def _weekday_point(self, weekday: int, rows: Sequence[DataRow]) -> WeekdayPoint:
        return WeekdayPoint(
            weekday=weekday,
            calendar_days=self._year.weekdays_reached(weekday),
            drinking_days=self._count_drinking_days(rows),
            stdav=sum(row.stdav for row in rows),
        )
