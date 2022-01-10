from datetime import datetime
from typing import Dict, List, Tuple

from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...counts.lib.stats import Stats as CountStats
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
        qs = models.Drink.objects.sum_by_day(self._year)
        past_latest_record = None

        try:
            qs_past = (
                models
                .Drink
                .objects
                .related()
                .filter(date__year__lt=self._year)
                .latest()
            )
            past_latest_record = qs_past.date
        except models.Drink.DoesNotExist:
            pass

        stats = CountStats(year=self._year, data=qs, past_latest=past_latest_record)
        data = stats.chart_calendar()
        context = {
            'chart_quantity': self.chart_quantity(),
            'chart_consumption': self.chart_consumption(),
            'chart_calendar_1H': self.chart_calendar(data[0:6], '1H'),
            'chart_calendar_2H': self.chart_calendar(data[6:], '2H'),
            'tbl_consumption': self.tbl_consumption(),
            'tbl_last_day': self.tbl_last_day(),
            'tbl_alcohol': self.tbl_alcohol(),
            'tbl_std_av': self.tbl_std_av(),
            'target_list': self.target_list(),
            'records': qs.count(),
        }
        return context

    def chart_quantity(self) -> str:
        r = render_to_string(
            'drinks/includes/chart_quantity.html',
            {'data': self._DrinkStats.quantity},
            self._request
        )
        return r

    def chart_consumption(self) -> str:
        r = render_to_string(
            'drinks/includes/chart_consumption.html', {
                'data': self._DrinkStats.consumption,
                'target': self._target,
                'avg': self._avg,
                'avg_label_y': self._avg_label_position(self._avg, self._target),
                'target_label_y': self._target_label_position(self._avg, self._target),
            },
            self._request
        )
        return r


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
