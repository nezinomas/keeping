from dataclasses import dataclass
from datetime import date, timedelta
from functools import cached_property

from ...core.lib.date import ydays
from .drinks_options import DrinkConverter
from .drinks_stats import DataRow


@dataclass(frozen=True)
class SlopeStats:
    direction: str  # "down" | "up" | "flat"
    pct: float  # magnitude of the fitted change over the window, always >= 0
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

    SLOPE_WINDOW = 90
    FLAT = "flat"

    def __init__(
        self,
        converter: DrinkConverter,
        current_daily: list[dict] | None = None,
        past_daily: list[dict] | None = None,
        target: float = 0.0,
        today: date | None = None,
    ):
        self._converter = converter
        self._target = target
        self._today = today or date.today()

        self._current = [DataRow(**row) for row in (current_daily or [])]
        self._past = [DataRow(**row) for row in (past_daily or [])]
        self.year = self._current[0].date.year if self._current else self._today.year

    @cached_property
    def _end_date(self) -> date:
        if self.year == self._today.year:
            return self._today
        return date(self.year, 12, 31)

    @cached_property
    def daily_ml(self) -> list[float]:
        """Dense day-by-day volume in ml (0 on days without records)."""
        by_date = {row.date: row.stdav for row in self._current}

        out = []
        day = date(self.year, 1, 1)
        while day <= self._end_date:
            out.append(self._converter.stdav_to_ml(by_date.get(day, 0.0)))
            day += timedelta(days=1)

        return out

    @cached_property
    def categories(self) -> list[str]:
        out = []
        day = date(self.year, 1, 1)
        while day <= self._end_date:
            out.append(day.isoformat())
            day += timedelta(days=1)

        return out

    def rolling(self, window: int) -> list[float]:
        values = self.daily_ml
        return [
            sum(values[max(0, i - window + 1) : i + 1])
            / len(values[max(0, i - window + 1) : i + 1])
            for i in range(len(values))
        ]

    def slope(self) -> SlopeStats:
        window = self.daily_ml[-self.SLOPE_WINDOW :]
        n = len(window)

        if n < 2:
            return SlopeStats(self.FLAT, 0.0, improving=False, has_data=False)

        slope, mean_y = self._linear_slope(window)
        change = abs(slope * (n - 1))
        pct = round(change / mean_y * 100, 1) if mean_y else 0.0

        if slope < 0:
            return SlopeStats("down", pct, improving=True, has_data=True)
        if slope > 0:
            return SlopeStats("up", pct, improving=False, has_data=True)
        return SlopeStats(self.FLAT, 0.0, improving=False, has_data=True)

    def ytd(self) -> YtdStats:
        day_of_year = self._end_date.timetuple().tm_yday
        current = self._sum_stdav(self._current, day_of_year)

        if not self._past:
            return YtdStats(current, 0.0, None, improving=False, has_past=False)

        past = self._sum_stdav(self._past, day_of_year)
        # magnitude only; direction is carried by `improving` (like SlopeStats)
        pct = round(abs(current - past) / past * 100, 1) if past else None

        return YtdStats(current, past, pct, improving=current < past, has_past=True)

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

    @staticmethod
    def _linear_slope(values: list[float]) -> tuple[float, float]:
        n = len(values)
        xs = range(n)
        mean_x = sum(xs) / n
        mean_y = sum(values) / n

        denom = sum((x - mean_x) ** 2 for x in xs)
        if not denom:
            return 0.0, mean_y

        numer = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values))
        return numer / denom, mean_y

    @staticmethod
    def _sum_stdav(rows: list[DataRow], day_of_year: int) -> float:
        return sum(
            row.stdav for row in rows if row.date.timetuple().tm_yday <= day_of_year
        )
