from datetime import date, timedelta
from decimal import Decimal
from typing import List

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import Case, Count, F, Q, Sum, When
from django.db.models.functions import (ExtractYear, TruncDay, TruncMonth,
                                        TruncYear)

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class ExpenseTypeQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('journal')
            .prefetch_related('expensename_set')
            .filter(journal=journal)
        )

    def items(self):
        return self.related()


class ExpenseNameQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('parent')
            .filter(parent__journal=journal)
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

    def items(self):
        return self.related()


class ExpenseQuerySet(SumMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('expense_type', 'expense_name', 'account')
            .filter(expense_type__journal=journal)
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

    def sum_by_month(self, year):
        return \
            self \
            .related() \
            .month_sum(year)

    def sum_by_month_and_type(self, year):
        return \
            self \
            .related() \
            .filter(date__year=year) \
            .annotate(cnt=Count('expense_type')) \
            .values('expense_type') \
            .annotate(date=TruncMonth('date')) \
            .values('date') \
            .annotate(c=Count('id')) \
            .annotate(sum=Sum('price')) \
            .order_by('date') \
            .values(
                'date',
                'sum',
                title=F('expense_type__title'))

    def sum_by_month_and_name(self, year):
        return \
            self \
            .related() \
            .filter(date__year=year) \
            .annotate(cnt=Count('expense_type')) \
            .values('expense_type') \
            .annotate(cnt=Count('expense_name')) \
            .values('expense_name') \
            .annotate(date=TruncMonth('date')) \
            .values('date') \
            .annotate(c=Count('id')) \
            .annotate(sum=Sum('price')) \
            .order_by('expense_name__title', 'date') \
            .values(
                'date',
                'sum',
                title=F('expense_name__title'),
                type_title=F('expense_type__title'))

    def sum_by_day_ant_type(self, year, month):
        return \
            self \
            .related() \
            .filter(date__year=year) \
            .filter(date__month=month) \
            .annotate(cnt_id=Count('id')) \
            .values('cnt_id') \
            .annotate(date=TruncDay('date')) \
            .values('date') \
            .annotate(sum=Sum('price')) \
            .annotate(
                exception_sum=Sum(
                    Case(
                        When(exception=1, then='price'), default=Decimal(0))
                )
            ) \
            .order_by('date') \
            .values(
                'date',
                'sum',
                'exception_sum',
                title=F('expense_type__title'))

    def sum_by_year(self):
        return self.related().year_sum()

    def filter_types(self, arr: List[int] = None):
        if arr:
            return self.filter(expense_type__in=arr)
        return self
    filter_types.queryset_only = True

    def sum_by_year_type(self, expense_type: List[int] = None):
        return \
            self \
            .related() \
            .annotate(cnt=Count('expense_type')) \
            .values('expense_type') \
            .filter_types(expense_type) \
            .annotate(date=TruncYear('date')) \
            .annotate(year=ExtractYear(F('date'))) \
            .annotate(sum=Sum('price')) \
            .order_by('year') \
            .values(
                'year',
                'sum',
                title=F('expense_type__title')
            )

    def filter_names(self, arr: List[int] = None):
        if arr:
            return self.filter(expense_name__in=arr)
        return self
    filter_names.queryset_only = True

    def sum_by_year_name(self, expense_name: List[int] = None):
        return \
            self \
            .related() \
            .annotate(cnt=Count('expense_name')) \
            .values('expense_name') \
            .filter_names(expense_name) \
            .annotate(date=TruncYear('date')) \
            .annotate(year=ExtractYear(F('date'))) \
            .annotate(sum=Sum('price')) \
            .order_by('year') \
            .values(
                'year',
                'sum',
                title=F('expense_name__title'),
                root=F('expense_name__parent__title')
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

    def expenses(self):
        '''
        method used only in post_save signal
        method sum prices by year
        '''
        return (
            self
            .related()
            .annotate(year=ExtractYear(F('date')))
            .values('year', 'account__title')
            .annotate(expenses=Sum('price'))
            .values('year', 'expenses', id=F('account__pk'))
            .order_by('year', 'id')
        )
