from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django_pandas.managers import DataFrameManager

from ..accounts.models import Account
from ..savings.models import SavingType


class TransactionQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('from_account', 'to_account')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()


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
    pd = DataFrameManager()


class SavingClose(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        SavingType,
        on_delete=models.PROTECT,
        related_name='close_from_savings'
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='close_to_accounts'
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
    pd = DataFrameManager()


class SavingChange(models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        SavingType,
        on_delete=models.PROTECT,
        related_name='change_from_savings'
    )
    to_account = models.ForeignKey(
        SavingType,
        on_delete=models.PROTECT,
        related_name='change_to_savings'
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
    pd = DataFrameManager()
