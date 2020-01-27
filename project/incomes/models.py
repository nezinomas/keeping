from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Sum, When
from django.db.models.functions import TruncMonth

from ..accounts.models import Account
from ..users.models import User
from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..core.models import TitleAbstract


class IncomeTypeQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
        )

    def items(self):
        return self.related()


class IncomeType(TitleAbstract):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='income_types'
    )

    # Managers
    objects = IncomeTypeQuerySet.as_manager()

    class Meta:
        unique_together = ['user', 'title']
        ordering = ['title']

class IncomeQuerySet(SumMixin, models.QuerySet):
    def related(self):
        user = utils.get_user()
        qs = (
            self
            .select_related('account', 'income_type')
            .filter(income_type__user=user)
        )
        return qs

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self):
        return self.related().all()

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
            self
            .related()
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
            .related()
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
            .related()
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
