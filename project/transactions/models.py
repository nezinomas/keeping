from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Sum, When

from ..accounts.models import Account
from ..core.mixins.queryset_sum import SumMixin
from ..savings.models import SavingType


class TransactionQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('from_account', 'to_account')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()

    def summary_from(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': from_account.title,
                'tr_from_past': Decimal(),
                'tr_from_now': Decimal()
            }
        '''
        return (
            self
            .annotate(cnt=Count('from_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                tr_from_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                tr_from_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0))
            )
            .values(
                'tr_from_past',
                'tr_from_now',
                title=models.F('from_account__title'))
        )

    def summary_to(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': to_account.title,
                'tr_to_past': Decimal(),
                'tr_to_now': Decimal()
            }
        '''
        return (
            self
            .annotate(cnt=Count('to_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                tr_to_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                tr_to_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0))
            )
            .values(
                'tr_to_past',
                'tr_to_now',
                title=models.F('to_account__title'))
        )


class Transaction(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='transactions_from'
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='transactions_to'
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        ordering = ['-date', 'price', 'from_account']
        indexes = [
            models.Index(fields=['from_account']),
            models.Index(fields=['to_account']),
        ]

    def __str__(self):
        return (
            '{} {}->{}: {}'.
            format(self.date, self.from_account, self.to_account, self.price)
        )

    objects = TransactionQuerySet.as_manager()


class SavingCloseQuerySet(SumMixin, TransactionQuerySet):
    def month_sum(self, year, month=None):
        summed_name = 'sum'

        return (
            super()
            .sum_by_month(
                year=year, month=month,
                summed_name=summed_name)
            .values('date', summed_name)
        )

    def summary_from(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': from_account.title,
                's_close_from_past': Decimal(),
                's_close_from_now': Decimal()
            }
        '''
        return (
            self
            .annotate(cnt=Count('from_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_close_from_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                s_close_from_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0))
            )
            .values(
                's_close_from_past',
                's_close_from_now',
                title=models.F('from_account__title'))
        )

    def summary_to(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': to_account.title,
                's_close_to_past': Decimal(),
                's_close_to_now': Decimal()
            }
        '''
        return (
            self
            .annotate(cnt=Count('to_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_close_to_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                s_close_to_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0))
            )
            .values(
                's_close_to_past',
                's_close_to_now',
                title=models.F('to_account__title'))
        )


class SavingClose(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        SavingType,
        on_delete=models.PROTECT,
        related_name='savings_close_from'
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='savings_close_to'
    )
    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        ordering = ['-date', 'price', 'from_account']
        indexes = [
            models.Index(fields=['from_account']),
            models.Index(fields=['to_account']),
        ]

    def __str__(self):
        return (
            '{} {}->{}: {}'.
            format(self.date, self.from_account, self.to_account, self.price)
        )

    objects = SavingCloseQuerySet.as_manager()


class SavingChangeQuerySet(TransactionQuerySet):
    def summary_from(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': from_account.title,
                's_change_from_past': Decimal(),
                's_change_from_now': Decimal()
                's_change_from_fee_past': Decimal(),
                's_change_from_fee_now': Decimal(),
            }
        '''
        return (
            self
            .annotate(cnt=Count('from_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_change_from_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                s_change_from_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0)),
                s_change_from_fee_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='fee'),
                        default=0)),
                s_change_from_fee_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='fee'),
                        default=0))
            )
            .values(
                's_change_from_past',
                's_change_from_now',
                's_change_from_fee_past',
                's_change_from_fee_now',
                title=models.F('from_account__title'))
        )

    def summary_to(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': to_account.title,
                's_change_to_past': Decimal(),
                's_change_to_now': Decimal()
            }
        '''
        return (
            self
            .annotate(cnt=Count('to_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_change_to_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                s_change_to_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0))
            )
            .values(
                's_change_to_past',
                's_change_to_now',
                title=models.F('to_account__title'))
        )


class SavingChange(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        SavingType,
        on_delete=models.PROTECT,
        related_name='savings_change_from'
    )
    to_account = models.ForeignKey(
        SavingType,
        on_delete=models.PROTECT,
        related_name='savings_change_to'
    )
    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        ordering = ['-date', 'price', 'from_account']
        indexes = [
            models.Index(fields=['from_account']),
            models.Index(fields=['to_account']),
        ]

    def __str__(self):
        return (
            '{} {}->{}: {}'.
            format(self.date, self.from_account, self.to_account, self.price)
        )

    objects = SavingChangeQuerySet.as_manager()
