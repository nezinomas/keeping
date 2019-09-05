from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django_pandas.managers import DataFrameManager

from ..accounts.models import Account
from ..core.models import TitleAbstract


class IncomeType(TitleAbstract):
    class Meta:
        ordering = ['title']


class IncomeQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('account')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()


class Income(models.Model):
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
        ordering = ['-date', 'price']

    def __str__(self):
        return str(self.date)

    # managers
    objects = IncomeQuerySet.as_manager()
    pd = DataFrameManager()
