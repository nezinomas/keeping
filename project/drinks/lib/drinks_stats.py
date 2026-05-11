import calendar
from dataclasses import dataclass
from datetime import date
from functools import cached_property

from ...core.lib.date import ydays
from ..lib.drinks_options import DrinkConverter


@dataclass(frozen=True)
class DataRow:
    date: date
    qty: float
    stdav: float


@dataclass(frozen=True)
class MonthlyStatsDTO:
    total_volume_ml: list[float]
    avg_daily_volume_ml: list[float]
    total_quantity: list[float]


@dataclass(frozen=True)
class YearlyStatsDTO:
    avg_daily_volume_ml: float
    total_quantity: float


class DrinkStats:
    def __init__(
        self,
        converter: DrinkConverter,
        data: list[dict] | None = None,
        today: date | None = None,
    ):
        self.converter = converter
        self.today = today or date.today()

        self.data = [DataRow(**row) for row in (data or [])]
        self.year = self.data[0].date.year if self.data else self.today.year

    @cached_property
    def monthly(self) -> MonthlyStatsDTO:
        monthly_stdav = [0.0] * 12
        monthly_qty = [0.0] * 12

        for row in self.data:
            m = row.date.month - 1
            monthly_stdav[m] += row.stdav
            monthly_qty[m] += row.qty

        # Convert stdav to ml and calculate daily averages
        total_volume_ml = [self.converter.stdav_to_ml(v) for v in monthly_stdav]
        avg_daily_volume_ml = [
            self._avg(v, calendar.monthrange(self.year, i)[1])
            for i, v in enumerate(total_volume_ml, 1)
        ]

        return MonthlyStatsDTO(
            total_volume_ml=total_volume_ml,
            avg_daily_volume_ml=avg_daily_volume_ml,
            total_quantity=monthly_qty,
        )

    @cached_property
    def yearly(self) -> YearlyStatsDTO:
        if not self.data:
            return YearlyStatsDTO(avg_daily_volume_ml=0.0, total_quantity=0.0)

        days_passed, month_limit = self._get_year_boundaries()
        total_volume = sum(self.monthly.total_volume_ml[:month_limit])
        total_quantity = sum(self.monthly.total_quantity[:month_limit])

        return YearlyStatsDTO(
            avg_daily_volume_ml=self._avg(total_volume, days_passed),
            total_quantity=total_quantity,
        )


    def _avg(self, total: float, days: int) -> float:
        return total / days if days else 0.0

    def _get_year_boundaries(self) -> tuple[int, int]:
        if self.year == self.today.year:
            return self.today.timetuple().tm_yday, self.today.month
        return ydays(self.year), 12
