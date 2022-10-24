import calendar
from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from ..lib.drinks_options import DrinksOptions
from ..managers import DrinkQuerySet
from .drinks_options import DrinksOptions


def empty_list():
    return [0.0 for _ in range(12)]


@dataclass
class DrinkStats:
    data: DrinkQuerySet.sum_by_month = None
    consumption: list[float] = \
        field(init=False, default_factory=empty_list)
    quantity: list[float] = \
        field(init=False, default_factory=empty_list)
    options: DrinksOptions = \
        field(init=False, default_factory=DrinksOptions)

    def __post_init__(self):
        if not self.data:
            return

        self._calc()

    def _calc(self) -> None:
        for row in self.data:
            _stdav = row.get('stdav')

            _date = row.get('date')
            _year = _date.year
            _month = _date.month
            _monthlen = calendar.monthrange(_year, _month)[1]

            idx = _month - 1

            self.consumption[idx] = \
                self.options.stdav_to_ml(_stdav) / _monthlen
            self.quantity[idx] = row.get('qty')
