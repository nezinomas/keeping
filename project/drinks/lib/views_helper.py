from datetime import datetime
from typing import Dict, List, Tuple

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...core.lib.translation import month_names
from .. import models
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
        data = DrinkStats(qs_drinks).consumption

        if not any(data):
            continue

        serries.append({'name': y, 'data': data})

    return serries


class RenderContext():
    def __init__(self, request: HttpRequest, year: int):
        self._request = request
        self._year = year

        self._target = self._get_target()

        self._avg, self._qty = self._get_avg_qty()
        self._DrinkStats = self._get_drink_stats()

    def chart_quantity(self) -> List[Dict]:
        return {
            'categories' : list(month_names().values()),
            'data' : self._DrinkStats.quantity,
            'text' : {'quantity': ('Quantity')}
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

    def chart_calendar(self, data: List[Dict], chart_id='F') -> str:
        rendered = render_to_string(
            'counts/includes/chart_calendar.html',
            {
                'data': data,
                'id': chart_id,
            },
            self._request
        )
        return rendered

    def tbl_consumption(self) -> str:
        r = render_to_string(
            'drinks/includes/tbl_consumption.html', {
                'qty': self._qty,
                'avg': self._avg,
                'target': self._target,
            },
            self._request
        )
        return r

    def tbl_last_day(self) -> str:
        r = render_to_string(
            'drinks/includes/tbl_last_day.html',
            self._dry_days(),
            self._request
        )
        return r

    def tbl_alcohol(self) -> str:
        obj = DrinksOptions()
        stdav = self._qty / obj.ratio

        r = render_to_string(
            'drinks/includes/tbl_alcohol.html', {
                'l': obj.stdav_to_alkohol(stdav)
            },
            self._request
        )
        return r

    def tbl_std_av(self) -> str:
        r = render_to_string(
            'drinks/includes/tbl_std_av.html', {
                'items': std_av(self._year, self._qty)
            },
            self._request
        )
        return r

    def _get_target(self):
        obj = DrinksOptions()
        qs = models.DrinkTarget.objects.year(self._year)

        return obj.stdav_to_ml(qs[0].quantity) if qs else 0

    def _get_drink_stats(self):
        qs = models.Drink.objects.sum_by_month(self._year)

        return DrinkStats(qs)

    def _get_avg_qty(self) -> Tuple[float, float]:
        qs = models.Drink.objects.drink_day_sum(self._year)
        avg = qs.get('per_day', 0) if qs else 0
        qty = qs.get('qty', 0) if qs else 0

        return (avg, qty)

    def _avg_label_position(self, avg: float, target: float) -> int:
        return 15 if target - 50 <= avg <= target else -5

    def _target_label_position(self, avg: float, target: float) -> int:
        return 15 if avg - 50 <= target <= avg else -5

    def _dry_days(self) -> Dict:
        qs = None
        try:
            qs = models.Drink.objects.year(self._year).latest()
        except models.Drink.DoesNotExist:
            pass

        # if current year has no record
        # try get latest record
        if not qs:
            try:
                qs = models.Drink.objects.related().latest()
            except models.Drink.DoesNotExist:
                pass

        if qs:
            latest = qs.date
            delta = (datetime.now().date() - latest).days
            return {'date': latest, 'delta': delta}

        return {}
