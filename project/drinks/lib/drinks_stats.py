import calendar
from datetime import datetime, date
from typing import Dict, List


class DrinkStats():
    def __init__(self, arr: List[Dict]):
        _list = [0.0 for x in range(0, 12)]

        self._consumsion = _list.copy()
        self._quantity = _list.copy()

        self._calc(arr)

    @property
    def consumsion(self) -> List[float]:
        return self._consumsion

    @property
    def quantity(self) -> List[float]:
        return self._quantity

    def _calc(self, arr: List[Dict]) -> None:
        if not arr:
            return

        for a in arr:
            idx = a.get('month', 1) - 1

            self._consumsion[idx] = a.get('per_month', 0)
            self._quantity[idx] = a.get('sum', 0)


def std_av(year: int, qty: float) -> List[Dict]:
    if not qty:
        return {}

    (day, week, month) = _dates(year)

    av = qty * 2.5

    a = {
        'total': av,
        'per_day': av / day,
        'per_week': av / week,
        'per_month': av / month
    }

    arr = [
        {'title': 'Std AV', **a},
        {'title': 'Alus, 0.5L', **{k: _beer(v) for k, v in a.items()}},
        {'title': 'Vynas, 1L', **{k: _wine(v) for k, v in a.items()}},
        {'title': 'Degtinė, 1L', **{k: _vodka(v) for k, v in a.items()}},
    ]

    return arr


def _beer(av: float) -> float:
    return (av * 200) / 500


def _wine(av: float) -> float:
    return (av * 100) / 1000


def _vodka(av: float) -> float:
    return (av * 25) / 1000


def _dates(year: int) -> (int, int, int):
    now = datetime.now().date()

    year = year if year else now.year

    _year = now.year
    _month = now.month
    _week = int(now.strftime("%V"))
    _day = now.timetuple().tm_yday

    if _year == year:
        return (_day, _week, _month)
    else:
        _days = 366 if calendar.isleap(year) else 365
        _weeks = date(year, 12, 28).isocalendar()[1]
        return (_days, _weeks, 12)
