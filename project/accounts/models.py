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
            qs = self._related().filter(year=year)
        else:
            qs = self._related()

        return qs.values(
            'year', 'past', 'balance', 'incomes',
            'expenses', 'have', 'delta',
            title=F('account__title')
        )


class AccountBalance(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='accounts_balance'
    )
    year = models.PositiveIntegerField(
        validators=[MinValueValidator(1974), MaxValueValidator(2050)]
    )
    past = models.FloatField(default=0.0)
    incomes = models.FloatField(default=0.0)
    expenses = models.FloatField(default=0.0)
    balance = models.FloatField(default=0.0)
    have = models.FloatField(default=0.0)
    delta = models.FloatField(default=0.0)

    # Managers
    objects = AccountBalanceQuerySet.as_manager()

    def __str__(self):
        return f'{self.account.title}'
