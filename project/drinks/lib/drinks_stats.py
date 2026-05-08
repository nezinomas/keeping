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
        per_month = [0.0] * 12
        per_day_of_month = [0.0] * 12
        qty_of_month = [0.0] * 12

        for row in self.data:
            month_idx = row.date.month - 1
            ml = self.converter.stdav_to_ml(row.stdav)

            per_month[month_idx] += ml
            qty_of_month[month_idx] += row.qty

        if self.year:
            for i in range(12):
                month_len = calendar.monthrange(self.year, i + 1)[1]
                per_day_of_month[i] = per_month[i] / month_len

        return MonthlyStatsDTO(
            total_volume_ml=per_month,
            avg_daily_volume_ml=per_day_of_month,
            total_quantity=qty_of_month,
        )

    @cached_property
    def yearly(self) -> YearlyStatsDTO:
        if not self.year or not self.data:
            return YearlyStatsDTO(avg_daily_volume_ml=0.0, total_quantity=0.0)

        if self.year == self.today.year:
            day_of_year = self.today.timetuple().tm_yday
            month_limit = self.today.month
        else:
            day_of_year = ydays(self.year)
            month_limit = 12

        total_ml = sum(self.monthly.total_volume_ml[:month_limit])

        return YearlyStatsDTO(
            avg_daily_volume_ml=total_ml / day_of_year if day_of_year else 0.0,
            total_quantity=sum(self.monthly.total_quantity),
        )
