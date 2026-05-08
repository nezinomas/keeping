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
    per_month: list[float]
    per_day_of_month: list[float]
    qty_of_month: list[float]


@dataclass(frozen=True)
class YearlyStatsDTO:
    per_day_of_year: float
    qty_of_year: float


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
            per_month=per_month,
            per_day_of_month=per_day_of_month,
            qty_of_month=qty_of_month,
        )

    @cached_property
    def yearly(self) -> YearlyStatsDTO:
        if not self.year or not self.data:
            return YearlyStatsDTO(per_day_of_year=0.0, qty_of_year=0.0)

        if self.year == self.today.year:
            day_of_year = self.today.timetuple().tm_yday
            month_limit = self.today.month
        else:
            day_of_year = ydays(self.year)
            month_limit = 12

        total_ml = sum(self.monthly.per_month[:month_limit])

        return YearlyStatsDTO(
            per_day_of_year=total_ml / day_of_year if day_of_year else 0.0,
            qty_of_year=sum(self.monthly.qty_of_month),
        )
