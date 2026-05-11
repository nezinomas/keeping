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
        self.year = self.data[0].date.year if self.data else 1974

    @cached_property
    def monthly(self) -> MonthlyStatsDTO:
        vols = [0.0] * 12
        qtys = [0.0] * 12

        for row in self.data:
            month = row.date.month - 1
            vols[month] += row.stdav
            qtys[month] += row.qty

        # Convert stdav to ml and calculate daily averages
        total_volume_ml = [self.converter.stdav_to_ml(v) for v in vols]
        avg_daily_volume_ml = [
            vol / calendar.monthrange(self.year, i)[1]
            for i, vol in enumerate(total_volume_ml, 1)
        ]

        return MonthlyStatsDTO(
            total_volume_ml=total_volume_ml,
            avg_daily_volume_ml=avg_daily_volume_ml,
            total_quantity=qtys,
        )

    @cached_property
    def yearly(self) -> YearlyStatsDTO:
        if not self.data:
            return YearlyStatsDTO(avg_daily_volume_ml=0.0, total_quantity=0.0)

        is_current = (self.year == self.today.year)
        days_passed = self.today.timetuple().tm_yday if is_current else ydays(self.year)
        limit = self.today.month if is_current else 12

        total_volume_ml = sum(self.monthly.total_volume_ml[:limit])
        total_quantity = sum(self.monthly.total_quantity[:limit])
        avg_daily_volume_ml = total_volume_ml / days_passed if days_passed else 0.0

        return YearlyStatsDTO(
            avg_daily_volume_ml=avg_daily_volume_ml,
            total_quantity=total_quantity,
        )
