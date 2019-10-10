import calendar
from datetime import date, datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (Case, Count, DateField, ExpressionWrapper, F,
                              FloatField, IntegerField, Model,
                              PositiveIntegerField, QuerySet, Sum, When)
from django.db.models.functions import (ExtractDay, ExtractMonth, TruncDate,
                                        TruncYear)

from ..core.mixins.queryset_sum import SumMixin


class DrinkQuerySet(SumMixin, QuerySet):
    def year(self, year):
        return self.filter(date__year=year)

    def items(self):
        return self.all()

    def month_sum(self, year, month=None):
        summed_name = 'sum'

        return (
            super()
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
                    output_field=IntegerField())
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

    def _per_period(self, qty: float, end: int) -> float:
        return ExpressionWrapper(
            ((qty * 0.5) / end) * 1000,
            output_field=FloatField()
        )


class Drink(Model):
    date = DateField()
    quantity = FloatField(
        validators=[MinValueValidator(0.1)]
    )

    objects = DrinkQuerySet.as_manager()

    def __str__(self):
        return f'{self.date}: {self.quantity}'

    class Meta:
        ordering = ['-date']
        get_latest_by = ['date']


class DrinkTargetQuerySet(SumMixin, QuerySet):
    def year(self, year):
        return self.filter(year=year)

    def items(self):
        return self.all()


class DrinkTarget(Model):
    year = PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)],
        unique=True
    )
    quantity = PositiveIntegerField()

    objects = DrinkTargetQuerySet.as_manager()

    def __str__(self):
        return f'{self.year}: {self.quantity}'

    class Meta:
        ordering = ['-year']
