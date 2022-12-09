from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse_lazy

from ..core.models import TitleAbstract
from ..journals.models import Journal
from . import managers


class PensionType(TitleAbstract):
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='pension_types'
    )
    created = models.DateTimeField(
        auto_now_add=True
    )

    # Managers
    objects = managers.PensionTypeQuerySet.as_manager()

    class Meta:
        unique_together = ['journal', 'title']
        ordering = ['title']

    def get_absolute_url(self):
        return reverse_lazy("pensions:type_update", kwargs={"pk": self.pk})

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

    # managers
    objects = managers.PensionQuerySet.as_manager()

    class Meta:
        ordering = ['-date', 'price']

    def __str__(self):
        return f'{(self.date)}: {self.pension_type}'

    def get_absolute_url(self):
        return reverse_lazy("pensions:update", kwargs={"pk": self.pk})

    def get_delete_url(self):
        return reverse_lazy("pensions:delete", kwargs={"pk": self.pk})


class PensionBalance(models.Model):
    pension_type = models.ForeignKey(
        PensionType,
        on_delete=models.CASCADE,
        related_name='pensions_balance'
    )
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    latest_check = models.DateTimeField(null=True, blank=True)
    past_amount = models.FloatField(default=0.0)
    past_fee = models.FloatField(default=0.0)
    fee = models.FloatField(default=0.0)
    per_year_incomes = models.FloatField(default=0.0)
    per_year_fee = models.FloatField(default=0.0)
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
