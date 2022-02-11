from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import Case, Count, F, Q, Sum, When
from django.db.models.functions import ExtractYear, TruncMonth

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class SavingTypeQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('journal')
            .filter(journal=journal)
        )

    def items(self, year=None):
        if year:
            _year = year
        else:
            _year = utils.get_user().year

        return (
            self
            .related()
            .filter(
                Q(closed__isnull=True) |
                Q(closed__gte=_year)
            )
        )


class SavingQuerySet(SumMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('account', 'saving_type')
            .filter(saving_type__journal=journal)
        )
        return qs

    def year(self, year):
        return (
            self
            .related()
            .filter(date__year=year))

    def items(self):
        return self.related()

    def sum_by_month(self, year, month=None):
        sum_annotation = 'sum'

        return (
            self
            .related()
            .month_sum(
                year=year,
                month=month,
                sum_annotation=sum_annotation)
            .values('date', sum_annotation)
        )

    def sum_by_month_and_type(self, year):
        return (
            self
            .related()
            .filter(date__year=year)
            .annotate(cnt=Count('saving_type'))
            .values('saving_type')
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(sum=Sum('price'))
            .order_by('saving_type__title', 'date')
            .values(
                'date',
                'sum',
                title=F('saving_type__title'))
        )

    def sum_by_day_and_type(self, year, month):
        sum_annotation = 'sum'

        return (
            self
            .related()
            .day_sum(
                year=year,
                month=month,
                sum_annotation=sum_annotation)
            .values(
                sum_annotation,
                'date',
                title=F('saving_type__title'))
        )

    def sum_by_day(self, year, month):
        sum_annotation = 'sum'

        return (
            self
            .related()
            .day_sum(
                year=year,
                month=month,
                sum_annotation=sum_annotation)
            .values(
                sum_annotation,
                'date')
        )

    def last_months(self, months: int = 6) -> float:
        # previous month
        # if today February, then start is 2020-01-31
        start = date.today().replace(day=1) - timedelta(days=1)

        # back months to past; if months=6 then end=2019-08-01
        end = (start + timedelta(days=1)) - relativedelta(months=months)

        qs = self.related().filter(date__range=(end, start)).aggregate(sum=Sum('price'))

        return qs

    def incomes(self):
        return (
            self
            .related()
            .annotate(year=ExtractYear(F('date')))
            .values('year', 'saving_type__title')
            .annotate(incomes=Sum('price'), fees=Sum('fee'))
            .values('year', 'incomes', 'fees', id=F('saving_type__pk'))
            .order_by('year', 'id')
        )

    def expenses(self):
        return (
            self
            .related()
            .annotate(year=ExtractYear(F('date')))
            .values('year', 'account__title')
            .annotate(expenses=Sum('price'))
            .values('year', 'expenses', id=F('account__pk'))
            .order_by('year', 'id')
        )


class SavingBalanceQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        journal = user.journal
        qs = (
            self
            .select_related('saving_type')
            .filter(saving_type__journal=journal)
        )
        return qs

    def items(self):
        return self.related()

    def year(self, year: int, types=None):
        qs = self.items().filter(year=year)

        if types:
            qs = qs.filter(saving_type__type__in=types)

        qs = qs.order_by('saving_type__type', 'saving_type__title')

        return qs.values(
            'year',
            'past_amount', 'past_fee',
            'fees', 'invested', 'incomes', 'market_value',
            'profit_incomes_proc', 'profit_incomes_sum',
            'profit_invested_proc', 'profit_invested_sum',
            title=F('saving_type__title'),
            type=F('saving_type__type')
        )

    def sum_by_type(self):
        return (
            self
            .related()
            .annotate(cnt=Count('saving_type'))
            .values('saving_type__type')
            .annotate(y=F('year'))
            .values('y')
            .annotate(invested=Sum('incomes'), profit=Sum('profit_incomes_sum'))
            .order_by('year')
            .values(
                'year',
                'invested',
                'profit',
                type=F('saving_type__type'))
        )

    def sum_by_year(self):
        return (
            self
            .related()
            .annotate(y=F('year'))
            .values('y')
            .annotate(invested=Sum('incomes'), profit=Sum('profit_incomes_sum'))
            .order_by('year')
            .values(
                'year',
                'invested',
                'profit'
            )
        )
