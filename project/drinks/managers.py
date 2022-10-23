from datetime import date
from typing import Dict, List

from django.db import models

from ..core.lib import utils
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

    def items(self):
        return self.related()

    def sum_by_year(self, year=None):
        return self \
            .related() \
            .year_sum(
                year=year,
                sum_annotation='qty',
                sum_column='quantity') \
            .order_by('date')

    def sum_by_month(self, year: int, month: int = None):
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'sum': float, 'month': int, 'monthlen': int, 'per_month': float}]
        """

        return \
            self \
            .related() \
            .month_sum(
                year=year,
                month=month,
                sum_annotation='qty',
                sum_column='quantity')\
            .order_by('date')

    def sum_by_day(self, year: int, month: int = None) -> List[Dict[date, float]]:
        qs = self \
            .related() \
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


class DrinkTargetQuerySet(SumMixin, models.QuerySet):
    def related(self):
        user = utils.get_user()
        return \
            self \
            .select_related('user') \
            .filter(user=user)

    def year(self, year):
        return \
            self \
            .related() \
            .filter(year=year)

    def items(self):
        return self.related()
