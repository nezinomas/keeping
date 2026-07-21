from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cached_property

from .drinks_stats import DataRow

# Medical harm-framing thresholds, all expressed in the canonical std av unit
# (1 std av = 10 g pure alcohol). The UK CMO low-risk guideline is 14 UK units
# per week for both sexes; a UK unit is 8 g, so 14 * 8 / 10 = 11.2 std av.
# The high-risk edge (~35 UK units) is a commonly cited "higher risk" marker
# in UK guidance, not a universal clinical cutoff for all drinkers.
WEEKLY_LOW_RISK_STDAV = 11.2
WEEKLY_HIGH_RISK_STDAV = 28.0
# A heavy drinking day: ~60 g alcohol in a single day. This is a daily total,
# not a single-occasion "binge" (which guidance defines per drinking session).
HEAVY_DAY_STDAV = 6.0


@dataclass(frozen=True)
class WeekPoint:
    label: str  # ISO date of the week-start (Monday)
    end: str  # ISO date of the week-end (Sunday)
    stdav: float


@dataclass(frozen=True)
class WeekZone:
    stdav: float
    state: str  # "low" | "medium" | "high"
    label: str  # ISO date of the week-start (Monday)
    end: str  # ISO date of the week-end (Sunday)
    has_data: bool = True


@dataclass(frozen=True)
class EmptyWeekZone:
    stdav: float = 0.0
    state: str = "empty"
    label: str = ""
    end: str = ""
    has_data: bool = False


@dataclass(frozen=True)
class CountComparison:
    current: int
    previous: int
    improving: bool
    has_past: bool = True


@dataclass(frozen=True)
class EmptyCountComparison:
    current: int
    previous: int = 0
    improving: bool = False
    has_past: bool = False


class RiskStats:
    """Alcohol harm-framing metrics derived from the daily (date, std av) series.

    Everything is measured in std av (medical units) so the guidelines apply
    regardless of the drink type selected elsewhere in the app.
    """

    def __init__(
        self,
        current_daily: Sequence[DataRow] = (),
        past_daily: Sequence[DataRow] = (),
        today: date | None = None,
    ):
        self._current = current_daily
        self._past = past_daily
        self._today = today or date.today()
        self.current_year = (
            self._current[0].date.year if self._current else self._today.year
        )

    @cached_property
    def _year_end_date(self) -> date:
        if self.current_year == self._today.year:
            return self._today
        return date(self.current_year, 12, 31)

    @staticmethod
    def _week_start(day: date) -> date:
        return day - timedelta(days=day.weekday())

    @staticmethod
    def _week_end(monday: date) -> date:
        return monday + timedelta(days=6)

    @staticmethod
    def _buckets(records: Iterable[DataRow]) -> dict[date, float]:
        acc: dict[date, float] = {}
        for row in records:
            monday = RiskStats._week_start(row.date)
            acc[monday] = acc.get(monday, 0.0) + row.stdav
        return acc

    @staticmethod
    def _zone(weekly_stdav: float) -> str:
        """Classify an already-rounded (1 dp) weekly total into a risk band."""
        if weekly_stdav > WEEKLY_HIGH_RISK_STDAV:
            return "high"
        if weekly_stdav > WEEKLY_LOW_RISK_STDAV:
            return "medium"
        return "low"

    @cached_property
    def _current_buckets(self) -> dict[date, float]:
        return self._buckets(self._current)

    @cached_property
    def _clipped_past(self) -> list[DataRow]:
        """Previous-year rows up to the same month/day as today, for a fair
        comparison. Matching on (month, day) rather than the ordinal
        day-of-year avoids misaligning the cutoff when the current and
        previous years have different lengths (a leap year on either side)."""
        cutoff = (self._year_end_date.month, self._year_end_date.day)
        return [row for row in self._past if (row.date.month, row.date.day) <= cutoff]

    @cached_property
    def _clipped_past_buckets(self) -> dict[date, float]:
        return self._buckets(self._clipped_past)

    def weekly_series(self) -> list[WeekPoint]:
        """Dense weekly totals from the first week of the year to the current week."""
        monday = self._week_start(date(self.current_year, 1, 1))
        last_monday = self._week_start(self._year_end_date)
        buckets = self._current_buckets

        series = []
        while monday <= last_monday:
            series.append(
                WeekPoint(
                    label=monday.isoformat(),
                    end=self._week_end(monday).isoformat(),
                    stdav=round(buckets.get(monday, 0.0), 1),
                )
            )
            monday += timedelta(days=7)
        return series

    def current_week(self) -> WeekZone:
        monday = self._week_start(self._year_end_date)
        stdav = round(self._current_buckets.get(monday, 0.0), 1)
        return WeekZone(
            stdav=stdav,
            state=self._zone(stdav),
            label=monday.isoformat(),
            end=self._week_end(monday).isoformat(),
        )

    def worst_week(self) -> WeekZone | EmptyWeekZone:
        buckets = self._current_buckets
        if not buckets:
            return EmptyWeekZone()

        monday, raw_stdav = max(buckets.items(), key=lambda item: item[1])
        stdav = round(raw_stdav, 1)
        return WeekZone(
            stdav=stdav,
            state=self._zone(stdav),
            label=monday.isoformat(),
            end=self._week_end(monday).isoformat(),
        )

    def _compare_counts(
        self, current: int, previous: int
    ) -> CountComparison | EmptyCountComparison:
        if not self._past:
            return EmptyCountComparison(current=current)
        return CountComparison(current, previous, improving=current < previous)

    def heavy_days(self) -> CountComparison | EmptyCountComparison:
        current = self._count_heavy(self._current)
        previous = self._count_heavy(self._clipped_past)
        return self._compare_counts(current, previous)

    def weeks_over_guideline(self) -> CountComparison | EmptyCountComparison:
        current = self._count_weeks_over(self._current_buckets)
        previous = self._count_weeks_over(self._clipped_past_buckets)
        return self._compare_counts(current, previous)

    def monthly_heavy_days(self) -> list[int]:
        counts = [0] * 12
        for row in self._current:
            if row.stdav > HEAVY_DAY_STDAV:
                counts[row.date.month - 1] += 1
        return counts

    @staticmethod
    def _count_heavy(records: Iterable[DataRow]) -> int:
        return sum(1 for row in records if row.stdav > HEAVY_DAY_STDAV)

    @staticmethod
    def _count_weeks_over(buckets: dict[date, float]) -> int:
        return sum(
            1 for total in buckets.values() if round(total, 1) > WEEKLY_LOW_RISK_STDAV
        )
