from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django_pandas.managers import DataFrameManager

from ..accounts.models import Account
from ..savings.models import SavingType


#
# Savings Worth
#
class SavingWorthQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('saving_type')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()

    def last_item(self):
        return self._related().last()


class SavingWorth(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    saving_type = models.ForeignKey(
        SavingType,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.date} - {self.saving_type}'

    # Managers
    objects = SavingWorthQuerySet.as_manager()
    pd = DataFrameManager()


#
# Accounts Worth
#
class AccountWorthQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('account')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()

    def last_item(self):
        return self._related().last()


class AccountWorth(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.date} - {self.account}'

    # Managers
    objects = AccountWorthQuerySet.as_manager()
    pd = DataFrameManager()
