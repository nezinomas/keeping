from datetime import date
from typing import Dict, List

from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User
from .apps import App_name as CounterAppName


class CounterQuerySet(SumMixin, models.QuerySet):
    App_name = CounterAppName

    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
            .filter(counter_type__iexact=self.App_name)
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
        #Returns
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


class Counter(models.Model):
    date = models.DateField()
    quantity = models.FloatField(
        validators=[MinValueValidator(0.1)]
    )
    counter_type = models.CharField(
        max_length=254,
        blank=False,
        validators=[MinLengthValidator(3)]
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    objects = CounterQuerySet.as_manager()

    def __str__(self):
        return f'{self.date}: {self.quantity}'

    class Meta:
        ordering = ['-date']
        get_latest_by = ['date']
