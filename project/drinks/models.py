import calendar
from datetime import date, datetime
from typing import Dict

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Count, ExpressionWrapper, F, Sum, When
from django.db.models.functions import ExtractMonth, ExtractYear, TruncYear

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..counters.models import Counter, CounterQuerySet
from ..users.models import User


class DrinkQuerySet(CounterQuerySet, models.QuerySet):
    def sum_by_month(self, year: int, month: int = None):
        #Returns
        # DrinkQuerySet [{'date': datetime.date, 'sum': float, 'month': int, 'monthlen': int, 'per_month': float}]
        #
        arr = []

        qs = super().sum_by_month(year, month)

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

            arr.append(item)

        return arr

    def day_sum(self, year: int) -> Dict[float, float]:
        # Returns
        # {'qty': float, 'per_day': float}

        arr = {}
        qs = super().sum_by_year(year)

        if qs.count() == 0:
            return arr

        _date = datetime.now().date()
        if year == _date.year:
            _day_of_year = _date.timetuple().tm_yday
        else:
            _day_of_year = 366 if calendar.isleap(year) else 365

        _qty = qs[0].get('qty')

        arr['qty'] = _qty
        arr['per_day'] = self._consumption(_qty, _day_of_year)

        return arr

    def summary(self):
        qs = (
            self
            .related()
            .annotate(c=Count('id'))
            .values('c')
            .annotate(date=TruncYear('date'))
            .annotate(year=ExtractYear(F('date')))
            .annotate(qty=Sum('quantity'))
            .values('year', 'qty')
            .order_by('year')
        )

        for row in qs:
            days = 366 if calendar.isleap(row.get('year')) else 365
            row['per_day'] = self._consumption(row.get('qty'), days)

        return qs

    def _per_period(self, qty: float, days: int) -> float:
        return ExpressionWrapper(
            self._consumption(qty, days),
            output_field=models.FloatField()
        )

    def _consumption(self, qty: float, days: int) -> float:
        return ((qty * 0.5) / days) * 1000


class Drink(Counter):
    objects = DrinkQuerySet.as_manager()

    class Meta:
        proxy = True


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


class DrinkTarget(models.Model):
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
    )
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='drink_targets'
    )

    objects = DrinkTargetQuerySet.as_manager()

    def __str__(self):
        return f'{self.year}: {self.quantity}'

    class Meta:
        ordering = ['-year']
        unique_together = ['year', 'user']
