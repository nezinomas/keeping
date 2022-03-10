from datetime import date, datetime
from typing import Dict, List, Tuple

from django.utils.translation import gettext as _

from ...core.lib.date import ydays
from .drinks_options import DrinksOptions


class DrinkStats():
    def __init__(self, arr: List[Dict]):
        _list = [0.0 for x in range(0, 12)]

        self._consumption = _list.copy()
        self._quantity = _list.copy()

        self._calc(arr)

    @property
    def consumption(self) -> List[float]:
        return self._consumption

    @property
    def quantity(self) -> List[float]:
        return self._quantity

    def _calc(self, arr: List[Dict]) -> None:
        if not arr:
            return

        for a in arr:
            idx = a.get('month', 1) - 1

            self._consumption[idx] = a.get('per_month', 0)
            self._quantity[idx] = a.get('sum', 0)


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

    arr = [
        {
            'title': 'Std Av',
            **{k: v * obj.stdav for k, v in a.items()}
        }, {
            'title': _('Beer') + ', 0.5L',
            **{k: obj.convert(v, 'beer') for k, v in a.items()}
        }, {
            'title': _('Wine') + ', 0.75L',
            **{k: obj.convert(v, 'wine') for k, v in a.items()}
        }, {
            'title': _('Vodka') + ', 1L',
            **{k: obj.convert(v, 'vodka') for k, v in a.items()}
        },
    ]

    return arr


def max_beer_bottles(year: int, max_quantity: int) -> float:
    _days = ydays(year)
    return (max_quantity * _days) / 500


def _dates(year: int) -> Tuple[int, int, int]:
    now = datetime.now().date()

    year = year if year else now.year

    _year = now.year
    _month = now.month
    _week = int(now.strftime("%V"))
    _day = now.timetuple().tm_yday

    if _year == year:
        return (_day, _week, _month)

    _days = ydays(year)
    _weeks = date(year, 12, 28).isocalendar()[1]

    return (_days, _weeks, 12)
