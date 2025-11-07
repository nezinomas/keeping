import calendar
from datetime import datetime
from typing import Optional

from ...core.lib.date import ydays
from ..lib.drinks_options import DrinksOptions


class DrinkStats:
    def __init__(self, options: DrinksOptions, data: Optional[list] = None):
        self.options = options
        self.data = data

        self.year = None
        self.per_month = [0.0] * 12
        self.per_day_of_month = [0.0] * 12
        self.per_day_of_year = 0.0
        self.qty_of_month = [0.0] * 12
        self.qty_of_year = 0.0

        self._calc_month()
        self._calc_year()

    def _calc_month(self) -> None:
        if not self.data:
            return

        for row in self.data:
            _stdav = row.get("stdav")
            _ml = self.options.stdav_to_ml(_stdav)

            _date = row.get("date")
            _year = _date.year
            _month = _date.month
            _monthlen = calendar.monthrange(_year, _month)[1]

            if not self.year:
                self.year = _year

            idx = _month - 1

            self.per_month[idx] = _ml
            self.per_day_of_month[idx] = _ml / _monthlen
            self.qty_of_month[idx] = row.get("qty")

    def _calc_year(self):
        if not self.data:
            return

        dt = datetime.now().date()

        if self.year == dt.year:
            day_of_year = dt.timetuple().tm_yday
            month = dt.month
        else:
            day_of_year = ydays(self.year)
            month = 12

        self.qty_of_year = sum(self.qty_of_month)
        self.per_day_of_year = sum(self.per_month[:month]) / day_of_year
