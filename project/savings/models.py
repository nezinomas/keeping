from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from ..accounts.models import Account
from ..core.mixins.account_balance import AccountBalanceMixin
from ..core.models import TitleAbstract
from ..journals.models import Journal
from . import managers


class SavingType(TitleAbstract):
    class Types(models.TextChoices):
        SHARES = 'shares', _('Shares')
        FUNDS = 'funds', _('Funds')
        PENSIONS = 'pensions', _('Pensions')

    created = models.DateTimeField(
        auto_now_add=True
    )
    closed = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='saving_types'
    )
    type = models.CharField(
        max_length=12,
        choices=Types.choices,
        default=Types.FUNDS,
    )

    # Managers
    objects = managers.SavingTypeQuerySet.as_manager()

    class Meta:
        unique_together = ['journal', 'title']
        ordering = ['type', 'title']


class Saving(AccountBalanceMixin, models.Model):
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
    objects = managers.SavingQuerySet.as_manager()


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
    objects = managers.SavingBalanceQuerySet.as_manager()

    def __str__(self):
        return f'{self.saving_type.title}'
