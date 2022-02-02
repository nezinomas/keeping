from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.mixins.account_balance import AccountBalanceMixin
from ..pensions.models import PensionType
from ..savings.models import SavingType
from . import managers


class SavingWorth(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE,
        related_name='savings_worth'
    )

    class Meta:
        get_latest_by = ['date']
        ordering = ['-date']

    def __str__(self):
        return f'{self.date:%Y-%m-%d %H:%M} - {self.saving_type}'

    # Managers
    objects = managers.SavingWorthQuerySet.as_manager()


class AccountWorth(AccountBalanceMixin, models.Model):
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='accounts_worth'
    )

    class Meta:
        get_latest_by = ['date']
        ordering = ['-date']

    def __str__(self):
        return f'{self.date:%Y-%m-%d %H:%M} - {self.account}'

    # Managers
    objects = managers.AccountWorthQuerySet.as_manager()


class PensionWorth(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.0'))]
    )
    pension_type = models.ForeignKey(
        PensionType,
        on_delete=models.CASCADE,
        related_name='pensions_worth'
    )

    class Meta:
        ordering = ['-date']
        get_latest_by = ['date']

    def __str__(self):
        return f'{self.date:%Y-%m-%d %H:%M} - {self.pension_type}'

    # Managers
    objects = managers.PensionWorthQuerySet.as_manager()
