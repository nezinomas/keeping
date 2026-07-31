from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from functools import cached_property

from ...core.lib.year_boundary import YearBoundary
from .drinks_stats import DataRow, EmptyYearOverYear, YearOverYear

WEEKDAYS = 7


@dataclass(frozen=True)
class WeekdayPoint:
    """One day of the week, as both a frequency and a severity.

    The two are independent and a year total answers neither: a weekday can be
    drunk on rarely and heavily, or often and lightly, and only the pair
    distinguishes them.
    """

    weekday: int  # 0 = Monday, matching date.weekday()
    calendar_days: int  # how many of that weekday the year has reached
    drinking_days: int
    stdav: float
    drinking_day_share: float  # drinking_days / calendar_days
    intensity: float  # stdav / drinking_days


class FrequencyStats:
    """When and how often — the shape counterpart to ``RiskStats`` (harm) and
    ``TrendStats`` (direction).

    Every average the app showed before this divided a year's total by all the
    days elapsed, which fuses two independent behaviours: how often a user
    drinks, and how much on a day they do. Drinking days answers the first,
    Intensity the second, and a year-over-year move in the total can finally be
    attributed to one of them.

    Intensity stays in Std Av whatever Drink type is selected, because it is
    read against ``HEAVY_DAY_STDAV`` and a threshold defined in Std Av only
    lines up with a figure in Std Av. Everything else here is a count of days
    or a ratio, so no drink-type conversion belongs anywhere in this module —
    ``DataRow.qty`` is deliberately never read.
    """

    def __init__(
        self,
        current_daily: Sequence[DataRow] = (),
        past_daily: Sequence[DataRow] = (),
        today: date | None = None,
    ):
        self._current_daily_records = current_daily
        self._past_daily_records = past_daily
        self._year = YearBoundary.from_records(current_daily, today)
        self.current_year = self._year.year

    @property
    def is_current_year(self) -> bool:
        """Whether the year under view is still running, so that a share of it
        is a share of the days elapsed and not of all 365."""
        return self._year.is_current

    @staticmethod
    def _count_drinking_days(records: Iterable[DataRow]) -> int:
        """Calendar days carrying a Drink, not rows: a day can hold several."""
        return len({row.date for row in records})

    @staticmethod
    def _intensity(records: Sequence[DataRow]) -> float:
        days = FrequencyStats._count_drinking_days(records)
        return sum(row.stdav for row in records) / days if days else 0.0

    @cached_property
    def drinking_days(self) -> int:
        return self._count_drinking_days(self._current_daily_records)

    @cached_property
    def dry_days(self) -> int:
        """Days of the year reached with no Drink on them — so today for the
        year running, Dec 31 for one already over."""
        return max(self._year.days_elapsed - self.drinking_days, 0)

    @cached_property
    def drinking_day_share(self) -> float:
        return self._share(self.drinking_days)

    @cached_property
    def dry_share(self) -> float:
        return self._share(self.dry_days)

    def _share(self, days: int) -> float:
        """A count of days as a fraction of the year reached.

        Both shares are 0.0 for a year with no Drinks at all: nothing was
        recorded, and a year nobody logged is not evidence of a year spent dry.
        """
        if not self._current_daily_records:
            return 0.0

        elapsed = self._year.days_elapsed
        return days / elapsed if elapsed else 0.0

    @cached_property
    def intensity(self) -> float:
        """Std Av per Drinking day — a year's total spread over the days it was
        actually drunk on, not over the days in the year."""
        return self._intensity(self._current_daily_records)

    @cached_property
    def _past_clipped_records(self) -> list[DataRow]:
        """Previous-year rows up to the same month and day as the year end."""
        return self._year.clip(self._past_daily_records)

    def _compare(
        self, current: float, previous: float
    ) -> YearOverYear | EmptyYearOverYear:
        return YearOverYear.compare(
            current, previous, has_past=bool(self._past_daily_records)
        )

    def compare_frequency(self) -> YearOverYear | EmptyYearOverYear:
        return self._compare(
            self.drinking_days, self._count_drinking_days(self._past_clipped_records)
        )

    def compare_intensity(self) -> YearOverYear | EmptyYearOverYear:
        return self._compare(
            self.intensity, self._intensity(self._past_clipped_records)
        )

    def _calendar_days_of(self, weekday: int) -> int:
        """How many of one weekday the year has reached.

        The denominator every rate below divides by, and it obeys the same year
        boundary as everything else: a running year has had more Mondays than
        Sundays if it started on a Monday, and counting all 52 would report a
        rate that has not happened yet.
        """
        elapsed = self._year.days_elapsed
        offset = (weekday - date(self._year.year, 1, 1).weekday()) % 7

        return (elapsed - offset - 1) // WEEKDAYS + 1 if offset < elapsed else 0

    def weekday_profile(self) -> list[WeekdayPoint]:
        """The year resolved by day of the week, Monday first.

        Always seven points: a weekday nobody drank on is a finding, and a chart
        with a missing column would read as a chart of six days.
        """
        by_weekday: list[list[DataRow]] = [[] for _ in range(WEEKDAYS)]
        for row in self._current_daily_records:
            by_weekday[row.date.weekday()].append(row)

        return [
            self._weekday_point(weekday, rows)
            for weekday, rows in enumerate(by_weekday)
        ]

    def _weekday_point(self, weekday: int, rows: Sequence[DataRow]) -> WeekdayPoint:
        calendar_days = self._calendar_days_of(weekday)
        drinking_days = self._count_drinking_days(rows)
        stdav = sum(row.stdav for row in rows)

        return WeekdayPoint(
            weekday=weekday,
            calendar_days=calendar_days,
            drinking_days=drinking_days,
            stdav=stdav,
            drinking_day_share=drinking_days / calendar_days if calendar_days else 0.0,
            intensity=stdav / drinking_days if drinking_days else 0.0,
        )
