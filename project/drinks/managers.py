import calendar
from datetime import datetime
from typing import Dict

from django.db import models

from ..core.lib import utils
from ..core.lib.date import ydays
from ..core.mixins.queryset_sum import SumMixin
from ..counters.managers import CounterQuerySet
from .apps import App_name as DrinksAppName


class DrinkQuerySet(CounterQuerySet):
    counter_type = DrinksAppName

    def sum_by_month(self, year: int, month: int = None):
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'sum': float, 'month': int, 'monthlen': int, 'per_month': float}]
        """

        qs = super().sum_by_month(year, month)

        arr = []
        for row in qs:
            _date = row.get('date')
            _month = _date.month
            _monthlen = calendar.monthrange(year, _month)[1]
            _qty = row.get('qty')

            item = {}
            item['date'] = _date
            item['sum'] = _qty
            item['month'] = _month
            item['monthlen'] = _monthlen
            item['per_month'] = self._consumption(_qty, _monthlen)

            if item:
                arr.append(item)

        return arr

    def drink_day_sum(self, year: int) -> Dict[float, float]:
        """
        Returns {'qty': float, 'per_day': float}
        """

        arr = {}
        qs = list(super().sum_by_year(year))

        if not qs:
            return arr

        _date = datetime.now().date()
        if year == _date.year:
            _day_of_year = _date.timetuple().tm_yday
        else:
            _day_of_year = ydays(year)

        _qty = qs[0].get('qty')

        arr['qty'] = _qty
        arr['per_day'] = self._consumption(_qty, _day_of_year)

        return arr

    def summary(self):
        #Returns
        # [{'year': int, 'qty': float, 'per_day': float}]

        qs = super().sum_by_year()

        arr = []
        for row in qs:
            _qty = row.get('qty')
            _date = row.get('date')
            _days = ydays(_date.year)

            item = {}
            item['year'] = _date.year
            item['qty'] = _qty
            item['per_day'] = self._consumption(_qty, _days)

            if item:
                arr.append(item)

        return arr

    def _consumption(self, qty: float, days: int) -> float:
        return ((qty * 0.5) / days) * 1000


class DrinkTargetQuerySet(SumMixin, models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
        )

    def year(self, year):
        return (
            self
            .related()
            .filter(year=year)
        )

    def items(self):
        return self.related()
