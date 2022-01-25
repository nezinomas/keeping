from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from ..accounts.models import Account, AccountBalance
from ..bookkeeping.lib import helpers as calc
from ..core.lib import utils
from ..core.mixins.from_db import MixinFromDbAccountId
from ..core.models import TitleAbstract
from ..core.signals import SignalBase
from ..journals.models import Journal
from .managers import IncomeQuerySet, IncomeTypeQuerySet


class IncomeType(TitleAbstract):
    class Types(models.TextChoices):
        SALARY = 'salary', _('Salary')
        DIVIDENTS = 'dividents', _('Dividents')
        OTHER = 'other', _('Other')

    journal = models.ForeignKey(
        Journal,
        on_delete=models.CASCADE,
        related_name='income_types'
    )
    type = models.CharField(
        max_length=12,
        choices=Types.choices,
        default=Types.SALARY,
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

    original_price = 0.0
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.pk:
            self.original_price = self.price

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        user = utils.get_user()
        journal = Journal.objects.get(pk=user.journal.pk)

        if journal.first_record > self.date:
            journal.first_record = self.date
            journal.save()

        try:
            _qs = (
                AccountBalance
                .objects
                .get(Q(year=self.date.year) & Q(account_id=self.account.pk))
            )

            _price = float(self.price)
            _original_price = float(self.original_price)

            _qs.incomes = _qs.incomes - _original_price + _price
            _qs.balance = calc.calc_balance([_qs.past, _qs.incomes, _qs.expenses])
            _qs.delta = calc.calc_delta([_qs.have, _qs.balance])

            _qs.save()

        except AccountBalance.DoesNotExist:
            SignalBase.accounts(sender=Income, instance=None)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        try:
            _qs = (
                AccountBalance
                .objects
                .get(Q(year=self.date.year) & Q(account_id=self.account.pk))
            )

            _price = float(self.price)

            _qs.incomes = _qs.incomes - _price
            _qs.balance = calc.calc_balance([_qs.past, _qs.incomes, _qs.expenses])
            _qs.delta = calc.calc_delta([_qs.have, _qs.balance])
            _qs.delta = _qs.have - _qs.balance

            _qs.save()

        except AccountBalance.DoesNotExist:
            SignalBase.accounts(sender=Income, instance=None)
