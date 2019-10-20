from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, F, When

from ..core.models import TitleAbstract


class AccountQuerySet(models.QuerySet):
    def items(self, year: int = None):
        return self


class Account(TitleAbstract):
    order = models.PositiveIntegerField(
        default=10
    )

    class Meta:
        ordering = ['order', 'title']

    # Managers
    objects = AccountQuerySet.as_manager()


class AccountBalanceQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('account')

    def items(self, year: int = None):
        if year:
            past = year - 1
            return (
                self
                ._related()
                .filter(year__lte=year, year__gte=past)
             )
        else:
            return self._related()


class AccountBalance(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='accounts_balance'
    )
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    incomes = models.FloatField(default=0.0)
    expenses = models.FloatField(default=0.0)
    delta = models.FloatField(default=0.0)
    have = models.FloatField(default=0.0)
    diff = models.FloatField(default=0.0)

    # Managers
    objects = AccountBalanceQuerySet.as_manager()

    def __str__(self):
        return f'{self.account.title}'
