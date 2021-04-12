from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta
from django.core.validators import (FileExtensionValidator, MinLengthValidator,
                                    MinValueValidator)
from django.db import models
from django.db.models import Case, Count, F, Q, Sum, When
from django.db.models.functions import (ExtractYear, TruncDay, TruncMonth,
                                        TruncYear)

from ..accounts.models import Account
from ..core.lib import utils
from ..core.mixins.from_db import MixinFromDbAccountId
from ..core.models import TitleAbstract
from ..users.models import User
from .helpers.models_helper import upload_attachment


class ExpenseTypeQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .prefetch_related('expensename_set')
            .filter(user=user)
        )

    def items(self):
        return self.related()


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


class ExpenseNameQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        qs = (
            self
            .select_related('parent')
            .filter(parent__user=user)
        )
        return qs

    def year(self, year):
        qs = (
            self
            .related()
            .filter(
                Q(valid_for__isnull=True) | Q(valid_for=year)
            ))
        return qs

    def parent(self, parent_id):
        return (
            self
            .related()
            .filter(parent_id=parent_id)
        )

    def items(self):
        return self.related()


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
    def related(self):
        user = utils.get_user()
        qs = (
            self
            .select_related('expense_type', 'expense_name', 'account')
            .filter(expense_type__user=user)
        )
        return qs

    def year(self, year):
        return (
            self
            .related()
            .filter(date__year=year)
        )

    def items(self):
        return self.related().all()

    def sum_by_month_and_type(self, year):
        return (
            self
            .related()
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

    def sum_by_month_and_name(self, year):
        return (
            self
            .related()
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

    def sum_by_day_ant_type(self, year, month):
        return (
            self
            .related()
            .filter(date__year=year)
            .filter(date__month=month)
            .annotate(cnt_id=Count('id'))
            .values('cnt_id')
            .annotate(date=TruncDay('date'))
            .values('date')
            .annotate(sum=Sum('price'))
            .annotate(
                exception_sum=Sum(
                    Case(
                        When(exception=1, then='price'), default=Decimal(0))
                )
            )
            .order_by('date')
            .values(
                'date',
                'sum',
                'exception_sum',
                title=F('expense_type__title'))
        )

    def sum_by_year(self):
        return (
            self
            .related()
            .annotate(c=Count('id'))
            .values('c')
            .annotate(date=TruncYear('date'))
            .annotate(year=ExtractYear(F('date')))
            .annotate(sum=Sum('price'))
            .order_by('year')
            .values('year', 'sum')
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
            .related()
            .annotate(cnt=Count('expense_type'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                e_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                e_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values('e_past', 'e_now', title=models.F('account__title'))
        )

    def last_months(self, months: int = 6) -> float:
        # previous month
        # if today February, then start is 2020-01-31
        start = date.today().replace(day=1) - timedelta(days=1)

        # back months to past; if months=6 then end=2019-08-01
        end = (start + timedelta(days=1)) - relativedelta(months=months)

        qs = (
            self
            .related()
            .filter(date__range=(end, start))
            .values('expense_type')
            .annotate(sum=Sum('price'))
            .values('sum', title=models.F('expense_type__title'))
        )

        return qs


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
