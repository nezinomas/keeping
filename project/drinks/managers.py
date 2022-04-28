import calendar
from datetime import date, datetime
from typing import Dict, List

from django.db import models

from ..core.lib import utils
from ..core.lib.date import ydays
from ..core.mixins.queryset_sum import SumMixin

from .lib.drinks_options import DrinksOptions


class DrinkQuerySet(SumMixin, models.QuerySet):
    def related(self):
        return (
            self
            .select_related('user')
            .filter(user=utils.get_user())
            .order_by('-date')
        )

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self, count_type=None):
        return self.related()

    def sum_by_month(self, year: int, month: int = None):
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'sum': float, 'month': int, 'monthlen': int, 'per_month': float}]
        """

        qs = self\
            .related()\
            .month_sum(
                year=year,
                month=month,
                sum_annotation='qty',
                sum_column='quantity')\
            .order_by('date')

        obj = DrinksOptions()
        ratio = obj.ratio

        arr = []
        for row in qs:
            _date = row.get('date')
            _month = _date.month
            _monthlen = calendar.monthrange(year, _month)[1]
            _qty = row.get('qty') * ratio
            _stdav = row.get('qty')

            item = {}
            item['date'] = _date
            item['sum'] = _qty
            item['month'] = _month
            item['monthlen'] = _monthlen
            item['per_month'] = obj.stdav_to_ml(stdav=_stdav) / _monthlen

            if item:
                arr.append(item)

        return arr

    def drink_day_sum(self, year: int) -> Dict[float, float]:
        """
        Returns {'qty': float, 'per_day': float}
        """

        arr = {}
        qs = self\
            .related()\
            .year_sum(
                year=year,
                sum_annotation='qty',
                sum_column='quantity')\
            .order_by('date')

        qs = list(qs)

        if not qs:
            return arr

        _date = datetime.now().date()
        if year == _date.year:
            _day_of_year = _date.timetuple().tm_yday
        else:
            _day_of_year = ydays(year)

        _obj = DrinksOptions()
        _qty = qs[0].get('qty') * _obj.ratio
        _stdav = qs[0].get('qty')

        arr['qty'] = _qty
        arr['per_day'] = _obj.stdav_to_ml(stdav=_stdav) / _day_of_year

        return arr

    def sum_by_day(self, year: int, month: int = None) -> List[Dict[date, float]]:
        qs = self\
            .related()\
            .day_sum(
                year=year,
                month=month,
                sum_annotation='qty',
                sum_column='quantity')\
            .order_by('date')

        ratio = DrinksOptions().ratio

        for q in qs:
            q['qty'] = q['qty'] * ratio

        return qs

    def summary(self):
        #Returns
        # [{'year': int, 'qty': float, 'per_day': float}]

        qs = self\
            .related()\
            .year_sum(
                year=None,
                sum_annotation='qty',
                sum_column='quantity')\
            .order_by('date')

        obj = DrinksOptions()
        ratio = obj.ratio

        arr = []
        for row in qs:
            _qty = row.get('qty') * ratio
            _stdav = row.get('qty')

            _date = row.get('date')
            _days = ydays(_date.year)

            item = {}
            item['year'] = _date.year
            item['qty'] = _qty
            item['per_day'] = obj.stdav_to_ml(drink_type=obj.drink_type, stdav=_stdav) / _days

            if item:
                arr.append(item)

        return arr


class DrinkTargetQuerySet(SumMixin, models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
        )

    def year(self, year):
        qs = (
            self
            .related()
            .filter(year=year)
        )

        return qs

    def items(self):
        return self.related()
