from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Sum, When
from django.db.models.functions import TruncMonth

from ..accounts.models import Account
from ..core.mixins.queryset_sum import SumMixin
from ..core.models import TitleAbstract


class IncomeType(TitleAbstract):
    class Meta:
        ordering = ['title']


class IncomeQuerySet(SumMixin, models.QuerySet):
    def _related(self):
        return self.select_related('account', 'income_type')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related().all()

    def income_sum(self, year: int, month: int=None) -> List[Dict[str, Any]]:
        '''
        year:
            filter data by year and return sums for every month
        month:
            filter data by year AND month, return sum for that month
        return:
            {'date': datetime.date(), 'sum': Decimal()}
        '''
        summed_name = 'sum'

        return (
            super()
            .sum_by_month(year, summed_name, month=month)
            .values('date', summed_name)
        )

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                'i_past': Decimal(),
                'i_now': Decimal()
            }
        '''
        return (
            self
            .annotate(cnt=Count('income_type'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                i_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                i_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0))
            )
            .values(
                'i_past',
                'i_now',
                title=models.F('account__title'),
                id=models.F('account__pk')
            )
        )

    def month_type_sum(self, year):
        return (
            self
            .filter(date__year=year)
            .annotate(cnt=Count('income_type'))
            .values('income_type')
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(sum=Sum('price'))
            .order_by('income_type__title', 'date')
            .values(
                'date',
                'sum',
                title=F('income_type__title'))
        )


class Income(models.Model):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    remark = models.TextField(
        max_length=1000,
        blank=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='incomes'
    )
    income_type = models.ForeignKey(
        IncomeType,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-date', 'price']
        indexes = [
            models.Index(fields=['account', 'income_type']),
            models.Index(fields=['income_type']),
        ]

    def __str__(self):
        return f'{(self.date)}: {self.income_type}'

    # managers
    objects = IncomeQuerySet.as_manager()
