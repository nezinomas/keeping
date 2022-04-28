from datetime import date
from typing import Dict, List

from django.db import models

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class CountQuerySet(SumMixin, models.QuerySet):
    def related(self):
        return (
            self
            .select_related('user')
            .filter(user=utils.get_user())
            .order_by('-date')
        )

    def year(self, year, count_type=None):
        qs = self.related()

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        qs = qs.filter(date__year=year)

        return qs

    def items(self, count_type=None):
        qs = self.related()
        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        return qs

    def sum_by_year(self, year=None, count_type=None):
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]
        qs = self.related()

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        qs = qs\
            .year_sum(
                year=year,
                sum_annotation='qty',
                sum_column='quantity')\
            .order_by('date')

        return qs

    def sum_by_month(self, year, count_type=None, month=None) -> List[Dict[date, float]]:
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]
        qs = self.related()

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        qs = qs\
            .month_sum(
                year=year,
                month=month,
                sum_annotation='qty',
                sum_column='quantity')\
            .order_by('date')

        return qs

    def sum_by_day(self, year, count_type=None, month=None) -> List[Dict[date, float]]:
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]
        qs = self.related()

        if count_type:
            qs = qs.filter(count_type__slug=count_type)

        qs = qs\
            .day_sum(
                year=year,
                month=month,
                sum_annotation='qty',
                sum_column='quantity')\
            .order_by('date')

        return qs


class CountTypeQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()

        return (
            self
            .select_related('user')
            .filter(user=user)
        )

    def items(self):
        return self.related()
