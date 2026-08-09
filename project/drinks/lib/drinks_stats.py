import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import cached_property

from ...core.lib.year_boundary import YearBoundary
from ..lib.drinks_options import DrinkConverter


@dataclass(frozen=True)
class DataRow:
    date: date
    qty: float
    stdav: float


@dataclass(frozen=True)
class MonthlyStatsDTO:
    # in the unit the selected drink type is shown in, not always ml
    total_volume: list[float | None]
    avg_daily_volume: list[float | None]
    total_quantity: list[float | None]


@dataclass(frozen=True)
class YearlyStatsDTO:
    avg_daily_volume: float
    total_quantity: float
    stdav: float = 0.0
    pure_alcohol_liters: float = 0.0
    avg_daily_stdav: float = 0.0


@dataclass(frozen=True)
class YearOverYear:
    """One figure this year beside the same figure last year, up to the same
    month and day.

    Shared by every lib that compares a year with the one before it, so a card
    reads the same four fields whether the figure is a count of days or an
    amount per day. How it is shown is the caller's: a count whole, an amount
    to the decimals its unit needs.
    """

    current: float
    previous: float
    improving: bool
    has_past: bool = True

    @classmethod
    def compare(
        cls, current: float, previous: float, *, has_past: bool
    ) -> "YearOverYear | EmptyYearOverYear":
        """Less is improving, which is true of every harm and frequency figure
        the app reports. A figure where more is better needs its own rule."""
        if not has_past:
            return EmptyYearOverYear(current=current)

        return cls(current, previous, improving=current < previous)


@dataclass(frozen=True)
class EmptyYearOverYear:
    current: float
    previous: float = 0.0
    improving: bool = False
    has_past: bool = False


class DrinkStats:
    def __init__(
        self,
        converter: DrinkConverter,
        data: Sequence[DataRow] = (),
        today: date | None = None,
    ):
        self.converter = converter
        self.data = data
        self._year = YearBoundary.from_records(data, today)
        self.year = self._year.year

    @cached_property
    def monthly(self) -> MonthlyStatsDTO:
        monthly_stdav = [0.0] * 12
        monthly_qty = [0.0] * 12

        for row in self.data:
            m = row.date.month - 1
            monthly_stdav[m] += row.stdav
            monthly_qty[m] += row.qty

        # into the unit it is shown in, then daily averages
        total_volume = [self.converter.stdav_to_display(v) for v in monthly_stdav]
        avg_daily_volume = [
            self._avg(v, calendar.monthrange(self.year, i)[1])
            for i, v in enumerate(total_volume, 1)
        ]

        return MonthlyStatsDTO(
            total_volume=self._to_boundary(total_volume),
            avg_daily_volume=self._to_boundary(avg_daily_volume),
            total_quantity=self._to_boundary(monthly_qty),
        )

    def _to_boundary(self, months: list[float]) -> list[float | None]:
        # a running year's December drawn as 0.0 cannot be told apart from a
        # December with no Drink in it, and a null is the only way to break a line
        reached = self._year.end_date.month

        return [value if m <= reached else None for m, value in enumerate(months, 1)]

    @cached_property
    def yearly(self) -> YearlyStatsDTO:
        if not self.data:
            return YearlyStatsDTO(
                avg_daily_volume=0.0,
                total_quantity=0.0,
                stdav=0.0,
                pure_alcohol_liters=0.0,
                avg_daily_stdav=0.0,
            )

        days_passed = self._year.days_elapsed
        month_limit = self._year.end_date.month
        total_volume = sum(self.monthly.total_volume[:month_limit])
        total_quantity = sum(self.monthly.total_quantity[:month_limit])
        stdav = total_quantity * self.converter.stdav_per_unit
        pure_alcohol_liters = self.converter.stdav_to_alcohol(stdav)

        return YearlyStatsDTO(
            avg_daily_volume=self._avg(total_volume, days_passed),
            total_quantity=total_quantity,
            stdav=stdav,
            pure_alcohol_liters=pure_alcohol_liters,
            avg_daily_stdav=self._avg(stdav, days_passed),
        )

    def _avg(self, total: float, days: int) -> float:
        return total / days if days else 0.0
