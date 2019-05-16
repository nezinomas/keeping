from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.models import TitleAbstract


class ExpenseName(TitleAbstract):
    class Meta:
        ordering = ['title']


class ExpenseSubName(TitleAbstract):
    parent = models.ForeignKey(
        ExpenseName,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['title']


class Expense(models.Model):
    date = models.DateField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    quantity = models.IntegerField(
        default=1,
    )
    category = models.ForeignKey(
        ExpenseName,
        on_delete=models.CASCADE
    )
    sub_category = models.ForeignKey(
        ExpenseSubName,
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
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.date)

    class Meta:
        ordering = ['-date']
