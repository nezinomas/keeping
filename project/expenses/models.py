from django.db.models import F, Q
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from ..accounts.models import Account
from ..core.models import TitleAbstract


class ExpenseTypeManager(models.Manager):
    def items(self, *args, **kwargs):
        return self.get_queryset().prefetch_related('expensename_set')


class ExpenseType(TitleAbstract):
    necessary = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ['title']

    objects = ExpenseTypeManager()


class ExpenseNameManager(models.Manager):
    def items(self, *args, **kwargs):
        qs = self.get_queryset()

        if 'parent_id' in kwargs:
            qs = qs.filter(parent_id=kwargs['parent_id'])

        if 'year' in kwargs:
            qs = qs.filter(
                Q(valid_for__isnull=True) |
                Q(valid_for=kwargs['year'])
            )

        return qs


class ExpenseName(TitleAbstract):
    title = models.CharField(
        max_length=254,
        blank=False,
    )
    valid_for = models.PositiveIntegerField(
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        ExpenseType,
        on_delete=models.CASCADE
    )

    objects = ExpenseNameManager()

    class Meta:
        unique_together = ('title', 'parent')
        ordering = [F('valid_for').desc(nulls_first=True), 'title']


class ExpenseManager(models.Manager):
    def items(self, *args, **kwargs):
        qs = (
            self.get_queryset().
            prefetch_related('expense_type', 'expense_name', 'account')
        )

        if 'year' in kwargs:
            qs = qs.filter(date__year=kwargs['year'])

        return qs


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
        on_delete=models.CASCADE
    )

    # Managers
    objects = ExpenseManager()

    def __str__(self):
        return str(self.date)

    class Meta:
        ordering = ['-date', 'expense_type', F('expense_name').asc(), 'price']
