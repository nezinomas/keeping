from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Q, Sum, When

from ..accounts.models import Account
from ..core.mixins.queryset_sum import SumMixin
from ..core.models import TitleAbstract


class SavingTypeQuerySet(models.QuerySet):
    def items(self, year: int = None):
        if not year:
            return self
        else:
            return (
                self
                .filter(
                    Q(closed__isnull=True) |
                    Q(closed__gte=year)
                )
            )


class SavingType(TitleAbstract):
    closed = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['title']

    # Managers
    objects = SavingTypeQuerySet.as_manager()


class SavingQuerySet(SumMixin, models.QuerySet):
    def _related(self):
        return self.select_related('account', 'saving_type')

    def _filter_closed(self, year):
        return (
            self
            .filter(
                Q(saving_type__closed__isnull=True) |
                Q(saving_type__closed__gte=year)
            )
        )

    def _summary(self, year):
        return (
            self
            ._filter_closed(year)
            .annotate(cnt=Count('saving_type'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                s_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0)),
                s_fee_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='fee'),
                        default=0)),
                s_fee_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='fee'),
                        default=0))
            )
        )

    def year(self, year):
        return (
            self._related()
            ._filter_closed(year)
            .filter(date__year=year))

    def items(self):
        return self._related()

    def month_saving(self, year, month=None):
        summed_name = 'sum'

        return (
            super()
            .sum_by_month(
                year=year, month=month,
                summed_name=summed_name)
            .values('date', summed_name)
        )

    def month_saving_type(self, year, month=None):
        summed_name = 'sum'

        return (
            super()
            .sum_by_month(
                year=year, month=month,
                summed_name=summed_name, groupby='saving_type')
            .values('date', summed_name, title=F('saving_type__title'))
        )

    def day_saving_type(self, year, month):
        summed_name = 'sum'

        return (
            super()
            .sum_by_day(
                year=year, month=month,
                summed_name=summed_name)
            .values(summed_name, 'date', title=F('saving_type__title'))
        )

    def day_saving(self, year, month):
        summed_name = 'sum'

        return (
            super()
            .sum_by_day(
                year=year, month=month,
                summed_name=summed_name)
            .values(summed_name, 'date')
        )

    def summary_from(self, year: int) -> List[Dict[str, Any]]:
        '''
        summary for accounts
        return:
            {
                'title': ACCOUNT,
                's_past': Decimal(),
                's_now': Decimal()
            }
        '''
        return (
            self
            ._summary(year)
            .values(
                's_past', 's_now',
                title=models.F('account__title'),
            )
        )

    def summary_to(self, year: int) -> List[Dict[str, Any]]:
        '''
        summary for saving_types
        return:
            {
                'title': SAVING_TYPE,
                's_past': Decimal(),
                's_now': Decimal(),
                's_fee_past': Decimal(),
                's_free_now': Decimal()
            }
        '''
        return (
            self
            ._summary(year)
            .values(
                's_past', 's_now',
                's_fee_past', 's_fee_now',
                title=models.F('saving_type__title'),
            )
        )


class Saving(models.Model):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    remark = models.TextField(
        max_length=1000,
        blank=True
    )
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='savings'
    )

    class Meta:
        ordering = ['-date', 'saving_type']
        indexes = [
            models.Index(fields=['account', 'saving_type']),
            models.Index(fields=['saving_type']),
        ]

    def __str__(self):
        return f'{self.date}: {self.saving_type}'

    # Managers
    objects = SavingQuerySet.as_manager()


class SavingBalanceQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('saving_type')

    def items(self, year: int = None):
        if year:
            qs = self._related().filter(year=year)
        else:
            qs = self._related()

        return qs.values(
            'year',
            'past_amount', 'past_fee',
            'fees', 'invested', 'incomes', 'market_value',
            'profit_incomes_proc', 'profit_incomes_sum',
            'profit_invested_proc', 'profit_invested_sum',
            title=F('saving_type__title')
        )


class SavingBalance(models.Model):
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE,
        related_name='savings_balance'
    )
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    past_amount = models.FloatField(default=0.0)
    past_fee = models.FloatField(default=0.0)
    fees = models.FloatField(default=0.0)
    invested = models.FloatField(default=0.0)
    incomes = models.FloatField(default=0.0)
    market_value = models.FloatField(default=0.0)
    profit_incomes_proc = models.FloatField(default=0.0)
    profit_incomes_sum = models.FloatField(default=0.0)
    profit_invested_proc = models.FloatField(default=0.0)
    profit_invested_sum = models.FloatField(default=0.0)

    # Managers
    objects = SavingBalanceQuerySet.as_manager()

    def __str__(self):
        return f'{self.saving_type.title}'
