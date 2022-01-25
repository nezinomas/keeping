from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from ..accounts.models import Account
from ..core.lib import utils
from ..core.mixins.from_db import MixinFromDbAccountId
from ..core.models import TitleAbstract
from ..journals.models import Journal
from .managers import IncomeQuerySet, IncomeTypeQuerySet
from ..core.mixins.balance import AccountBalanceMixin


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

        AccountBalanceMixin(sender=Income,
                            field_name='incomes',
                            caller='save',
                            year=self.date.year,
                            account_pk=self.account.pk,
                            price=self.price,
                            original_price=self.original_price)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        AccountBalanceMixin(sender=Income,
                            field_name='incomes',
                            caller='delete',
                            year=self.date.year,
                            account_pk=self.account.pk,
                            price=self.price)
