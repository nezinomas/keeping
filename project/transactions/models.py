from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.mixins.old_values import OldValuesMixin
from ..savings.models import SavingType
from . import managers


class Transaction(OldValuesMixin, models.Model):
    date = models.DateField()
    from_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transactions_from'
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
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

    objects = managers.TransactionQuerySet.as_manager()


class SavingClose(OldValuesMixin, models.Model):
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

    objects = managers.SavingCloseQuerySet.as_manager()


class SavingChange(OldValuesMixin, models.Model):
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

    objects = managers.SavingChangeQuerySet.as_manager()
