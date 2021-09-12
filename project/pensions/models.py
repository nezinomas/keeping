from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Sum, When

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..core.models import TitleAbstract
from ..journals.models import Journal
from . import managers

class PensionType(TitleAbstract):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='pension_types'
    )

    # Managers
    objects = managers.PensionTypeQuerySet.as_manager()

    class Meta:
        unique_together = ['journal', 'title']
        ordering = ['title']


class Pension(models.Model):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))]
    )
    remark = models.TextField(
        max_length=1000,
        blank=True
    )
    pension_type = models.ForeignKey(
        PensionType,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-date', 'price']

    def __str__(self):
        return f'{(self.date)}: {self.pension_type}'

    # managers
    objects = managers.PensionQuerySet.as_manager()


class PensionBalance(models.Model):
    pension_type = models.ForeignKey(
        PensionType,
        on_delete=models.CASCADE,
        related_name='pensions_balance'
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
    objects = managers.PensionBalanceQuerySet.as_manager()

    def __str__(self):
        return f'{self.pension_type.title}'
