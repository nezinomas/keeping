import calendar
from dataclasses import dataclass
from datetime import date, datetime

from ...core.lib.date import ydays
from ..lib.drinks_options import DrinkConverter


@dataclass
class DataRow:
    date: date
    qty: float
    stdav: float


class DrinkStats:
    def __init__(self, options: DrinkConverter, data: list | None = None):
        self.options = options

        self.year = None
        self.per_month = [0.0] * 12
        self.per_day_of_month = [0.0] * 12
        self.per_day_of_year = 0.0
        self.qty_of_month = [0.0] * 12
        self.qty_of_year = 0.0

        if not data:
            return

        self.year = data[0]["date"].year
        self.data = [DataRow(**row) for row in data]
        self._calc_month()
        self._calc_year()

    def _calc_month(self) -> None:
        for row in self.data:
            month_idx = row.date.month - 1
            ml = self.options.stdav_to_ml(row.stdav)
            month_len = calendar.monthrange(row.date.year, row.date.month)[1]

            self.per_month[month_idx] = ml
            self.per_day_of_month[month_idx] = ml / month_len
            self.qty_of_month[month_idx] = row.qty

    def _calc_year(self) -> None:
        today = datetime.now().date()

        if self.year == today.year:
            day_of_year = today.timetuple().tm_yday
            month_limit = today.month
        else:
            day_of_year = ydays(self.year)
            month_limit = 12

        total_ml = sum(self.per_month[:month_limit])
        self.per_day_of_year = total_ml / day_of_year if day_of_year else 0.0
        self.qty_of_year = sum(self.qty_of_month)
