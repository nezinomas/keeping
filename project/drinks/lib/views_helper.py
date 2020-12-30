from datetime import datetime
from typing import Dict, Tuple

from django.http import HttpRequest
from django.template.loader import render_to_string

from .. import models
from .drinks_stats import DrinkStats, max_beer_bottles, std_av


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
    def __init__(self, request: HttpRequest):
        self._request = request
        self._year = self._request.user.year

        self._target_qs = models.DrinkTarget.objects.year(self._year)
        self._target = self._get_target()

        self._avg, self._qty = self._get_avg_qty()
        self._DrinkStats = self._get_drink_stats()

    def context_to_reload(self) -> Dict[str, str]:
        context = {
            'chart_quantity': self.chart_quantity,
            'chart_consumsion': self.chart_consumsion(),
            'tbl_consumsion': self.tbl_consumsion(),
            'tbl_last_day': self.tbl_last_day(),
            'tbl_alcohol': self.tbl_alcohol(),
            'tbl_std_av': self.tbl_std_av(),
            'target_list': self.target_list(),
        }
        return context

    def chart_quantity(self) -> str:
        r = render_to_string(
            'drinks/includes/chart_quantity_per_month.html',
            {'data': self._DrinkStats.quantity},
            self._request
        )
        return r

    def chart_consumsion(self) -> str:
        r = render_to_string(
            'drinks/includes/chart_consumsion_per_month.html', {
                'data': self._DrinkStats.consumption,
                'target': self._target,
                'avg': self._avg,
                'avg_label_y': self._avg_label_position(self._avg, self._target),
                'target_label_y': self._target_label_position(self._avg, self._target),
            },
            self._request
        )
        return r

    def tbl_consumsion(self) -> str:
        r = render_to_string(
            'drinks/includes/tbl_consumsion.html', {
                'qty': self._qty,
                'avg': self._avg,
                'target': self._target
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
        r = render_to_string(
            'drinks/includes/tbl_alcohol.html', {
                'l': self._qty * 0.025
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

    def target_list(self) -> str:
        r = render_to_string(
            'drinks/includes/drinks_target_list.html',
            {
                'items': self._target_qs,
                'max_bottles': max_beer_bottles(self._year, self._target)
            },
            self._request)
        return r

    def _get_target(self):
        qs = self._target_qs
        return qs[0].quantity if qs else 0

    def _get_drink_stats(self):
        qs = models.Drink.objects.sum_by_month(self._year)

        return DrinkStats(qs)

    def _get_avg_qty(self) -> Tuple[float, float]:
        qs = models.Drink.objects.day_sum(self._year)
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

        if qs:
            latest = qs.date
            delta = (datetime.now().date() - latest).days
            return {'date': latest, 'delta': delta}

        return {}
