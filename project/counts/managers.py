from datetime import date
from typing import Dict, List

from django.db import models

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class CountQuerySet(models.QuerySet):
    counter_type = None

    def related(self, user: User = None, counter_type=None):
        if not user:
            user = utils.get_user()

        # set counter_type then editing counter title
        self.counter_type = counter_type if counter_type else self.counter_type

        if not self.counter_type:
            self.counter_type = utils.get_request_kwargs('slug')

        return (
            self
            .select_related('user')
            .filter(user=user)
            .filter(counter_type__iexact=self.counter_type)
            .order_by('-date')
        )

    def year(self, year, user: User = None):
        return (
            self
            .related(user)
            .filter(date__year=year)
        )

    def items(self, user: User = None):
        return self.related(user)

    def sum_by_year(self, year: int = None) -> List[Dict[date, float]]:
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]

        return (
            self
            .related()
            .year_sum(
                year=year,
                sum_annotation='qty',
                sum_column='quantity')
            .order_by('date')
        )

    def sum_by_month(self, year: int, month: int = None) -> List[Dict[date, float]]:
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]

        return (
            self
            .related()
            .month_sum(
                year=year,
                month=month,
                sum_annotation='qty',
                sum_column='quantity')
            .order_by('date')
        )

    def sum_by_day(self, year: int, month: int = None) -> List[Dict[date, float]]:
        # Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]

        return (
            self
            .related()
            .day_sum(
                year=year,
                month=month,
                sum_annotation='qty',
                sum_column='quantity')
            .order_by('date')
        )


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
