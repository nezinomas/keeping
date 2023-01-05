import calendar
from dataclasses import dataclass, field
from datetime import datetime

from ...core.lib.date import ydays
from ..lib.drinks_options import DrinksOptions
from ..managers import DrinkQuerySet
from .drinks_options import DrinksOptions


def empty_list():
    return [0.0 for _ in range(12)]


@dataclass
class DrinkStats:
    data: DrinkQuerySet.sum_by_month = None
    per_month: list[float] = \
        field(init=False, default_factory=empty_list)
    per_day_of_month: list[float] = \
        field(init=False, default_factory=empty_list)
    per_day_of_year: float = \
        field(init=False, default=0.0)
    qty_of_month: list[float] = \
        field(init=False, default_factory=empty_list)
    qty_of_year: float = \
        field(init=False, default=0.0)
    options: DrinksOptions = \
        field(init=False, default_factory=DrinksOptions)

    year: int = \
        field(init=False, default=None)

    def __post_init__(self):
        if not self.data:
            return

        self._calc_month()
        self._calc_year()

    def _calc_month(self) -> None:
        for row in self.data:
            _stdav = row.get('stdav')
            _ml = self.options.stdav_to_ml(_stdav)

            _date = row.get('date')
            _year = _date.year
            _month = _date.month
            _monthlen = calendar.monthrange(_year, _month)[1]

            if not self.year:
                self.year = _year

            idx = _month - 1

            self.per_month[idx] = _ml
            self.per_day_of_month[idx] = _ml / _monthlen
            self.qty_of_month[idx] = row.get('qty')

    def _calc_year(self):
        dt = datetime.now().date()

        if self.year == dt.year:
            day_of_year = dt.timetuple().tm_yday
            month = dt.month
        else:
            day_of_year = ydays(self.year)
            month = 12

        self.qty_of_year = sum(self.qty_of_month)
        self.per_day_of_year = sum(self.per_month[:month]) / day_of_year
