from datetime import date
from typing import Dict, List

from django.core.validators import MinValueValidator
from django.db import models

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..core.models import TitleAbstract
from ..users.models import User
from .apps import App_name as CounterAppName


class CounterTypeQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
        )


class CounterType(TitleAbstract):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='counter_types'
    )

    class Meta:
        unique_together = ['user', 'title']
        ordering = ['title']

    objects = CounterTypeQuerySet.as_manager()


class CounterQuerySet(SumMixin, models.QuerySet):
    App_name = CounterAppName

    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('counter_type')
            .filter(counter_type__user=user)
            .filter(counter_type__title__iexact=self.App_name)
            .order_by('-date')
        )

    def year(self, year):
        return (
            self
            .related()
            .filter(date__year=year)
        )

    def items(self):
        return self.related()

    def sum_by_year(self, year: int = None) -> List[Dict[date, float]]:
        #Returns
        # QuerySet [{'date': datetime.date, 'qty': float}]

        summed_name = 'qty'

        return (
            self
            .related()
            .year_sum(
                year=year,
                summed_name=summed_name,
                sum_column_name='quantity')
            .order_by('date')
        )

    def sum_by_month(self, year: int, month: int = None) -> List[Dict[date, float]]:
        #
        # returns QuerySet [{'date': datetime.date, 'qty': float}]
        #

        return (
            self
            .related()
            .month_sum(
                year=year,
                month=month,
                summed_name='qty',
                sum_column_name='quantity')
            .order_by('date')
        )


class Counter(models.Model):
    date = models.DateField()
    quantity = models.FloatField(
        validators=[MinValueValidator(0.1)]
    )
    counter_type = models.ForeignKey(
        CounterType,
        on_delete=models.CASCADE,
        related_name='counters'
    )

    objects = CounterQuerySet.as_manager()

    def __str__(self):
        return f'{self.date}: {self.quantity}'

    class Meta:
        ordering = ['-date']
        get_latest_by = ['date']
