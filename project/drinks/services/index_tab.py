from datetime import date, datetime
from typing import Dict, List, Tuple

from django.utils.translation import gettext as _

from ...core.lib.date import ydays
from ...core.lib.translation import month_names
from .. import models
from ..lib.drinks_options import DrinksOptions
from ..lib.drinks_stats import DrinkStats


def drink_type_dropdown(request):
    drink_type = request.user.drink_type

    return {
        'select_drink_type': zip(models.DrinkType.labels, models.DrinkType.values),
        'current_drink_type': models.DrinkType(drink_type).label,
    }

def several_years_consumption(years):
    serries = []
    for y in years:
        qs_drinks = models.Drink.objects.sum_by_month(int(y))
        if not qs_drinks:
            continue

        data = DrinkStats(qs_drinks).per_day_of_month

        if not any(data):
            continue

        serries.append({'name': y, 'data': data})

    return serries


class RenderContext():
    def __init__(self,
                 drink_stats: DrinkStats,
                 target: float = 0.0,
                 latest_past_date: date = None,
                 latest_current_date: date = None):
        self._options = DrinksOptions()

        self.drink_stats = drink_stats
        self._year = drink_stats.year
        self.target = target
        self.per_day_of_year = drink_stats.per_day_of_year
        self.quantity_of_year = drink_stats.qty_of_year
        self.latest_past_date = latest_past_date
        self.latest_current_date = latest_current_date

    def chart_quantity(self) -> List[Dict]:
        return {
            'categories' : list(month_names().values()),
            'data' : self.drink_stats.qty_of_month,
            'text' : {'quantity': _('Quantity')}
        }

    def chart_consumption(self) -> str:
        return {
            'categories' : list(month_names().values()),
            'data': self.drink_stats.per_day_of_month,
            'target': self.target,
            'avg': self.per_day_of_year,
            'avg_label_y':
                self._avg_label_position(self.per_day_of_year, self.target),
            'target_label_y':
                self._target_label_position(self.per_day_of_year, self.target),
            'text': {
                'limit': _('Limit'),
                'alcohol': _('Alcohol consumption per day, ml'),
            },
        }

    def tbl_consumption(self) -> str:
        return {
            'qty': self.quantity_of_year,
            'avg': self.per_day_of_year,
            'target': self.target,
        }

    def tbl_alcohol(self) -> str:
        stdav = self.quantity_of_year / self._options.ratio

        return {
            'liters': self._options.stdav_to_alcohol(stdav)
        }

    def tbl_std_av(self) -> str:
        return {
            'items': self._std_av(self._year, self.quantity_of_year)
        }

    def _avg_label_position(self, avg: float, target: float) -> int:
        return 15 if target - 50 <= avg <= target else -5

    def _target_label_position(self, avg: float, target: float) -> int:
        return 15 if avg - 50 <= target <= avg else -5

    def tbl_dry_days(self) -> Dict:
        _dict = {}

        if latest := self.latest_current_date or self.latest_past_date:
            delta = (datetime.now().date() - latest).days
            _dict = {'date': latest, 'delta': delta}

        return _dict

    def _std_av(self, year: int, qty: float) -> List[Dict]:
        if not qty:
            return {}

        (day, week, month) = self._dates(year)

        a = {
            'total': qty,
            'per_day': qty / day,
            'per_week': qty / week,
            'per_month': qty / month
        }

        return [
            {
                'title': _('Beer') + ', 0.5L',
                **{k: self._options.convert(v, 'beer') for k, v in a.items()}
            }, {
                'title': _('Wine') + ', 0.75L',
                **{k: self._options.convert(v, 'wine') for k, v in a.items()}
            }, {
                'title': _('Vodka') + ', 1L',
                **{k: self._options.convert(v, 'vodka') for k, v in a.items()}
            }, {
                'title': 'Std Av',
                **{k: v * self._options.stdav for k, v in a.items()}
            },
        ]

    def _dates(self, year: int) -> Tuple[int, int, int]:
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
