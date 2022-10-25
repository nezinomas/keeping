from datetime import date, datetime
from typing import Dict, List, Tuple

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...core.lib.date import ydays
from ...core.lib.translation import month_names
from .. import models
from .drinks_options import DrinksOptions
from .drinks_stats import DrinkStats


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

        data = DrinkStats(qs_drinks).consumption

        if not any(data):
            continue

        serries.append({'name': y, 'data': data})

    return serries


class RenderContext():
    def __init__(self,
                 request: HttpRequest,
                 year: int,
                 drink_stats: DrinkStats,
                 target: float = 0.0,
                 per_day_of_year: float = 0.0,
                 quantity_of_year: float = 0.0,
                 latest_past_date: date = None,
                 latest_current_date: date = None):
        self._request = request
        self._year = year

        self._target = target

        self._per_day_of_year = per_day_of_year
        self._quantity_of_year = quantity_of_year

        self._DrinkStats = drink_stats
        self.latest_past_date = latest_past_date
        self.latest_current_date = latest_current_date

    def chart_quantity(self) -> List[Dict]:
        return {
            'categories' : list(month_names().values()),
            'data' : self._DrinkStats.quantity,
            'text' : {'quantity': _('Quantity')}
        }

    def chart_consumption(self) -> str:
        return {
            'categories' : list(month_names().values()),
            'data': self._DrinkStats.consumption,
            'target': self._target,
            'avg': self._per_day_of_year,
            'avg_label_y':
                self._avg_label_position(self._per_day_of_year, self._target),
            'target_label_y':
                self._target_label_position(self._per_day_of_year, self._target),
            'text': {
                'limit': _('Limit'),
                'alcohol': _('Alcohol consumption per day, ml'),
            },
        }

    def tbl_consumption(self) -> str:
        return render_to_string(
            'drinks/includes/tbl_consumption.html', {
                'qty': self._quantity_of_year,
                'avg': self._per_day_of_year,
                'target': self._target,
            },
            self._request
        )

    def tbl_last_day(self) -> str:
        return render_to_string(
            'drinks/includes/tbl_last_day.html',
            self._dry_days(),
            self._request
        )

    def tbl_alcohol(self) -> str:
        obj = DrinksOptions()
        stdav = self._quantity_of_year / obj.ratio

        return render_to_string(
            'drinks/includes/tbl_alcohol.html', {
                'l': obj.stdav_to_alcohol(stdav)
            },
            self._request
        )

    def tbl_std_av(self) -> str:
        return render_to_string(
            'drinks/includes/tbl_std_av.html', {
                'items': self._std_av(self._year, self._quantity_of_year)
            },
            self._request
        )

    def _avg_label_position(self, avg: float, target: float) -> int:
        return 15 if target - 50 <= avg <= target else -5

    def _target_label_position(self, avg: float, target: float) -> int:
        return 15 if avg - 50 <= target <= avg else -5

    def _dry_days(self) -> Dict:
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

        obj = DrinksOptions()

        return [
            {
                'title': _('Beer') + ', 0.5L',
                **{k: obj.convert(v, 'beer') for k, v in a.items()}
            }, {
                'title': _('Wine') + ', 0.75L',
                **{k: obj.convert(v, 'wine') for k, v in a.items()}
            }, {
                'title': _('Vodka') + ', 1L',
                **{k: obj.convert(v, 'vodka') for k, v in a.items()}
            }, {
                'title': 'Std Av',
                **{k: v * obj.stdav for k, v in a.items()}
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
