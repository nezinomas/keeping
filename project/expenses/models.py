from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from ..accounts.models import Account
from ..core.mixins.queryset_sum import SumMixin
from ..core.models import TitleAbstract


class ExpenseTypeQuerySet(models.QuerySet):
    def _related(self):
        return self.prefetch_related('expensename_set')

    def items(self):
        return self._related()


class ExpenseType(TitleAbstract):
    necessary = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ['title']

    # Managers
    objects = ExpenseTypeQuerySet.as_manager()


class ExpenseNameQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('parent')

    def year(self, year):
        return self._related().filter(
            Q(valid_for__isnull=True) |
            Q(valid_for=year)
        )

    def parent(self, parent_id):
        return self._related().filter(parent_id=parent_id)

    def items(self):
        return self._related()


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

    class Meta:
        unique_together = ('title', 'parent')
        ordering = [F('valid_for').desc(nulls_first=True), 'title']

    # Managers
    objects = ExpenseNameQuerySet.as_manager()


class ExpenseQuerySet(SumMixin, models.QuerySet):
    def _related(self):
        return self.select_related('expense_type', 'expense_name', 'account')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related()

    def expense_sum(self, year, summed_name):
        return super().sum_by_month(year, summed_name)


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
        on_delete=models.CASCADE,
        related_name='expenses'
    )

    class Meta:
        ordering = ['-date', 'expense_type', F('expense_name').asc(), 'price']

    def __str__(self):
        return str(self.date)

    # Managers
    objects = ExpenseQuerySet.as_manager()
