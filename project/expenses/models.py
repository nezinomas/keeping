from decimal import Decimal
from typing import Any, Dict, List

from django.core.validators import MinLengthValidator, MinValueValidator
from django.db import models
from django.db.models import Case, Count, F, Q, Sum, When
from django.db.models.functions import TruncDay, TruncMonth

from ..accounts.models import Account
from ..auths.models import User
from ..core.lib.utils import get_user
from ..core.models import TitleAbstract


class ExpenseTypeQuerySet(models.QuerySet):
    def _related(self):
        user = get_user()

        return (
            self.prefetch_related('expensename_set')
            .filter(user=user))

    def items(self):
        return self._related()


class ExpenseType(TitleAbstract):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expense_types'
    )
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
        return self._related().all()


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


class ExpenseQuerySet(models.QuerySet):
    def _related(self):
        return self.select_related('expense_type', 'expense_name', 'account')

    def year(self, year):
        return self._related().filter(date__year=year)

    def items(self):
        return self._related().all()

    def month_expense_type(self, year):
        return (
            self
            .filter(date__year=year)
            .annotate(cnt=Count('expense_type'))
            .values('expense_type')
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(sum=Sum('price'))
            .order_by('date')
            .values(
                'date',
                'sum',
                title=F('expense_type__title'))
        )

    def month_name_sum(self, year):
        return (
            self
            .filter(date__year=year)
            .annotate(cnt=Count('expense_type'))
            .values('expense_type')
            .annotate(cnt=Count('expense_name'))
            .values('expense_name')
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(sum=Sum('price'))
            .order_by('expense_name__title', 'date')
            .values(
                'date',
                'sum',
                title=F('expense_name__title'),
                type_title=F('expense_type__title'))
        )

    def day_expense_type(self, year, month):
        return (
            self
            .filter(date__year=year)
            .filter(date__month=month)
            .annotate(cnt_id=Count('id'))
            .values('cnt_id')
            .annotate(date=TruncDay('date'))
            .values('date')
            .annotate(sum=Sum('price'))
            .annotate(
                exception_sum=Sum(
                    Case(When(exception=1, then='price'), default=0.0))
            )
            .order_by('date')
            .values(
                'date',
                'sum',
                'exception_sum',
                title=F('expense_type__title'))
        )

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': account.title,
                'e_past': Decimal(),
                'e_now': Decimal()
            }
        '''
        return (
            self
            .annotate(cnt=Count('expense_type'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                e_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=0)),
                e_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=0))
            )
            .values('e_past', 'e_now', title=models.F('account__title'))
        )


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
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['expense_type']),
            models.Index(fields=['expense_name']),
        ]

    def __str__(self):
        return f'{(self.date)}/{self.expense_type}/{self.expense_name}'

    # Managers
    objects = ExpenseQuerySet.as_manager()
