from decimal import Decimal

from django.core.validators import (FileExtensionValidator, MinLengthValidator,
                                    MinValueValidator)
from django.db import models
from django.db.models import F

from ..accounts.models import Account
from ..core.mixins.from_db import MixinFromDbAccountId
from ..core.models import TitleAbstract
from ..users.models import User
from .helpers.models_helper import upload_attachment
from .managers import ExpenseNameQuerySet, ExpenseQuerySet, ExpenseTypeQuerySet


class ExpenseType(TitleAbstract):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expense_types'
    )
    necessary = models.BooleanField(
        default=False
    )

    # Managers
    objects = ExpenseTypeQuerySet.as_manager()

    class Meta:
        unique_together = ['user', 'title']
        ordering = ['title']


class ExpenseName(TitleAbstract):
    title = models.CharField(
        max_length=254,
        blank=False,
        validators=[MinLengthValidator(3)]
    )
    valid_for = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        ExpenseType,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('title', 'parent')
        ordering = [F('valid_for').desc(nulls_first=True), 'title']

    # Managers
    objects = ExpenseNameQuerySet.as_manager()


class Expense(MixinFromDbAccountId):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    quantity = models.IntegerField(
        default=1,
    )
    expense_type = models.ForeignKey(
        ExpenseType,
        on_delete=models.CASCADE
    )
    expense_name = models.ForeignKey(
        ExpenseName,
        on_delete=models.CASCADE
    )
    remark = models.TextField(
        max_length=1000,
        blank=True
    )
    exception = models.BooleanField(
        default=False
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    attachment = models.FileField(
        blank=True,
        upload_to=upload_attachment,
        validators=[FileExtensionValidator(['txt', 'pdf', 'jpg', 'xls', 'xlsx', 'doc', 'docx'])],
    )

    class Meta:
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['expense_type']),
            models.Index(fields=['expense_name']),
        ]

    def __str__(self):
        return f'{(self.date)}/{self.expense_type}/{self.expense_name}'

    # Managers
    objects = ExpenseQuerySet.as_manager()
