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
        self.data = [DataRow(**row) for row in data] if data else []
        self.year = self.data[0].date.year if self.data else None

        self.today = today or date.today()

    @cached_property
    def monthly(self) -> MonthlyStatsDTO:
        if not self.year:
            return MonthlyStatsDTO(
                total_volume_ml=[0.0] * 12,
                avg_daily_volume_ml=[0.0] * 12,
                total_quantity=[0.0] * 12,
            )

        total_volume_ml = [0.0] * 12
        total_quantity = [0.0] * 12

        # Aggregate totals
        for row in self.data:
            month_idx = row.date.month - 1
            total_volume_ml[month_idx] += self.converter.stdav_to_ml(row.stdav)
            total_quantity[month_idx] += row.qty

        # Calculate daily averages
        avg_daily_volume_ml = [
            vol / calendar.monthrange(self.year, month_num)[1]
            for month_num, vol in enumerate(total_volume_ml, start=1)
        ]

        return MonthlyStatsDTO(
            total_volume_ml=total_volume_ml,
            avg_daily_volume_ml=avg_daily_volume_ml,
            total_quantity=total_quantity,
        )

    @cached_property
    def yearly(self) -> YearlyStatsDTO:
        if not self.year or not self.data:
            return YearlyStatsDTO(avg_daily_volume_ml=0.0, total_quantity=0.0)

        # Determine the time boundaries (Current year vs Past year)
        if self.year == self.today.year:
            days_passed = self.today.timetuple().tm_yday
            month_limit = self.today.month
        else:
            days_passed = ydays(self.year)
            month_limit = 12

        # Calculate totals and averages
        total_volume_ml = sum(self.monthly.total_volume_ml[:month_limit])
        total_quantity = sum(self.monthly.total_quantity)
        avg_daily_volume_ml = total_volume_ml / days_passed if days_passed else 0.0

        return YearlyStatsDTO(
            avg_daily_volume_ml=avg_daily_volume_ml,
            total_quantity=total_quantity,
        )
