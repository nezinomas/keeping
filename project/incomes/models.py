from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.mixins.from_db import MixinFromDbAccountId
from ..core.models import TitleAbstract
from ..journals.models import Journal
from .managers import IncomeQuerySet, IncomeTypeQuerySet


class IncomeType(TitleAbstract):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='income_types'
    )

    # Managers
    objects = IncomeTypeQuerySet.as_manager()

    class Meta:
        unique_together = ['journal', 'title']
        ordering = ['title']


class Income(MixinFromDbAccountId):
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
        indexes = [
            models.Index(fields=['account', 'income_type']),
            models.Index(fields=['income_type']),
        ]

    def __str__(self):
        return f'{(self.date)}: {self.income_type}'

    # managers
    objects = IncomeQuerySet.as_manager()
