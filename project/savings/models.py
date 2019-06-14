from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django_pandas.managers import DataFrameManager

from ..accounts.models import Account
from ..core.models import TitleAbstract


class SavingType(TitleAbstract):
    class Meta:
        ordering = ['title']


class SavingQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('account', 'saving_type')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()


class Saving(models.Model):
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
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-date', 'saving_type']

    def __str__(self):
        return str(self.saving_type)

    # Managers
    objects = SavingQuerySet.as_manager()
    pd = DataFrameManager()
