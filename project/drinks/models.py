import calendar
from datetime import date, datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Count, ExpressionWrapper, F, Sum, When
from django.db.models.functions import ExtractMonth, TruncYear, ExtractYear

from ..users.models import User
from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class DrinkQuerySet(SumMixin, models.QuerySet):
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
            .filter(date__year=year)
        )

    def items(self):
        return self.related()

    def month_sum(self, year, month=None):
        summed_name = 'sum'

        return (
            self
            .related()
            .sum_by_month(
                year=year, month=month,
                summed_name=summed_name, sum_column_name='quantity')
            .order_by('date')
            .annotate(month=ExtractMonth('date'))
            .annotate(
                monthlen=Case(
                    *[When(date__month=i, then=calendar.monthlen(year, i))
                        for i in range(1, 13)],
                    default=1,
                    output_field=models.IntegerField())
            )
            .annotate(
                per_month=self._per_period(F('sum'), F('monthlen')))
        )

    def day_sum(self, year):
        start = date(year, 1, 1)

        if year == datetime.now().date().year:
            end = datetime.now().date()
            day_of_year = end.timetuple().tm_yday
        else:
            end = date(year, 12, 31)
            day_of_year = 366 if calendar.isleap(year) else 365

        qs = (
            self
            .related()
            .filter(date__range=(start, end))
            .annotate(c=Count('id'))
            .values('c')
            .annotate(date=TruncYear('date'))
            .annotate(
                qty=Sum('quantity'),
                per_day=self._per_period(F('qty'), day_of_year))
            .values('qty', 'per_day')
        )

        return qs[0] if qs else {}

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


class Drink(models.Model):
    date = models.DateField()
    quantity = models.FloatField(
        validators=[MinValueValidator(0.1)]
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='drinks'
    )

    objects = DrinkQuerySet.as_manager()

    def __str__(self):
        return f'{self.date}: {self.quantity}'

    class Meta:
        ordering = ['-date']
        get_latest_by = ['date']


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
