import contextlib
from datetime import datetime, date
from typing import Dict, List, Tuple

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...core.lib.translation import month_names, weekday_names
from .. import models
from ..services.history import HistoryService
from .drinks_options import DrinksOptions
from .drinks_stats import DrinkStats, std_av


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
    def __init__(self, request: HttpRequest, year: int, drink_stats: DrinkStats, latest_past_date: date = None, latest_current_date: date = None):
        self._request = request
        self._year = year

        self._target = self._get_target()

        self._avg, self._qty = self._get_avg_qty()
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
            'avg': self._avg,
            'avg_label_y': self._avg_label_position(self._avg, self._target),
            'target_label_y': self._target_label_position(self._avg, self._target),
            'text': {
                'limit': _('Limit'),
                'alcohol': _('Alcohol consumption per day, ml'),
            },
        }

    def chart_calendar(self, data: List[Dict]) -> str:
        return {
            'data': data,
            'categories': [x[0] for x in list(weekday_names().values())],
            'text' : {
                'gap': _('Gap'),
                'quantity': _('Quantity'),
            }
        }

    def tbl_consumption(self) -> str:
        return render_to_string(
            'drinks/includes/tbl_consumption.html', {
                'qty': self._qty,
                'avg': self._avg,
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
        stdav = self._qty / obj.ratio

        return render_to_string(
            'drinks/includes/tbl_alcohol.html', {
                'l': obj.stdav_to_alcohol(stdav)
            },
            self._request
        )

    def tbl_std_av(self) -> str:
        return render_to_string(
            'drinks/includes/tbl_std_av.html', {
                'items': std_av(self._year, self._qty)
            },
            self._request
        )

    def _get_target(self):
        obj = DrinksOptions()
        qs = models.DrinkTarget.objects.year(self._year)

        return obj.stdav_to_ml(qs[0].quantity) if qs else 0

    def _get_avg_qty(self) -> Tuple[float, float]:
        qs = models.Drink.objects.sum_by_year(self._year)
        obj = HistoryService(qs)

        return (obj.current_year_per_day, obj.current_year_quantity)

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
