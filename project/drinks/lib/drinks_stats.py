import calendar
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, List, Tuple

from django.utils.translation import gettext as _

from ...core.lib.date import ydays
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
            _stdav = row.get('qty')

            _date = row.get('date')
            _year = _date.year
            _month = _date.month
            _monthlen = calendar.monthrange(_year, _month)[1]

            idx = _month - 1

            self.consumption[idx] = self.options.stdav_to_ml(
                _stdav) / _monthlen
            self.quantity[idx] = _stdav * self.options.ratio


def std_av(year: int, qty: float) -> List[Dict]:
    if not qty:
        return {}

    (day, week, month) = _dates(year)

    a = {
        'total': qty,
        'per_day': qty / day,
        'per_week': qty / week,
        'per_month': qty / month
    }

    obj = DrinksOptions()

    return [
        {
            'title': _('Beer') + ', 0.5L',
            **{k: obj.convert(v, 'beer') for k, v in a.items()}
        },
        {
            'title': _('Wine') + ', 0.75L',
            **{k: obj.convert(v, 'wine') for k, v in a.items()}
        },
        {
            'title': _('Vodka') + ', 1L',
            **{k: obj.convert(v, 'vodka') for k, v in a.items()}
        },
        {
            'title': 'Std Av',
            **{k: v * obj.stdav for k, v in a.items()}
        },
    ]


def _dates(year: int) -> Tuple[int, int, int]:
    now = datetime.now().date()
    year = year or now.year

    _year = now.year
    _month = now.month
    _week = int(now.strftime("%V"))
    _day = now.timetuple().tm_yday

    if _year == year:
        return (_day, _week, _month)

    _days = ydays(year)
    _weeks = date(year, 12, 28).isocalendar()[1]

    return (_days, _weeks, 12)
