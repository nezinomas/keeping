from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

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

    def __str__(self):
        return (
            '{} {}->{} {}'.
            format(self.date, self.from_account, self.to_account, self.price)
        )

    objects = TransactionQuerySet.as_manager()


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

    def __str__(self):
        return (
            '{} {}->{} {}'.
            format(self.date, self.from_account, self.to_account, self.price)
        )

    objects = SavingCloseQuerySet.as_manager()


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

    def __str__(self):
        return (
            '{} {}->{} {}'.
            format(self.date, self.from_account, self.to_account, self.price)
        )

    objects = TransactionQuerySet.as_manager()
