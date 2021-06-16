from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q

from ..journals.models import Journal
from ..core.lib import utils
from ..core.models import TitleAbstract


class AccountQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_journal()
        return (
            self
            .select_related('journal')
            .filter(journal=journal)
        )

    def items(self):
        journal = utils.get_journal()
        return (
            self
            .related()
            .filter(
                Q(closed__isnull=True) |
                Q(closed__gte=journal.year)
            )
        )


class Account(TitleAbstract):
    order = models.PositiveIntegerField(
        default=10
    )
    closed = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='accounts'
    )

    class Meta:
        unique_together = ['journal', 'title']
        ordering = ['order', 'title']

    # Managers
    objects = AccountQuerySet.as_manager()


class AccountBalanceQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_journal()
        qs = (
            self
            .select_related('account')
            .filter(account__journal=journal)
        )
        return qs

    def items(self):
        return self.related()

    def year(self, year: int):
        qs = (
            self
            .related()
            .filter(year=year)
            .order_by('account__title')
        )

        return qs.values(
            'pk',
            'year',
            'past',
            'balance',
            'incomes',
            'expenses',
            'have',
            'delta',
            title=F('account__title'),
            account_pk=F('account__pk')
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
