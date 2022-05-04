from typing import List

from django.db import models
from django.db.models import Count, F, Sum
from django.db.models.functions import ExtractYear, TruncMonth

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class IncomeTypeQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return \
            self \
            .select_related('journal') \
            .filter(journal=journal)

    def items(self):
        return self.related()


class IncomeQuerySet(SumMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return \
            self  \
            .select_related('account', 'income_type') \
            .filter(income_type__journal=journal)

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self):
        return self.related().all()

    def sum_by_year(self, income_type: List[str] = None):
        qs = self.related()

        if income_type:
            qs = qs.filter(income_type__type__in=income_type)

        qs = qs.year_sum()

        return qs

    def sum_by_month(self, year, month=None):
        return \
            self \
            .related() \
            .month_sum(year, month)

    def sum_by_month_and_type(self, year):
        return \
            self \
            .related() \
            .filter(date__year=year) \
            .annotate(cnt=Count('income_type')) \
            .values('income_type') \
            .annotate(date=TruncMonth('date')) \
            .values('date') \
            .annotate(c=Count('id')) \
            .annotate(sum=Sum('price')) \
            .order_by('income_type__title', 'date') \
            .values(
                'date',
                'sum',
                title=F('income_type__title'))

    def incomes(self):
        '''
        method used only in post_save signal
        method sum prices by year
        '''
        return \
            self \
            .related() \
            .annotate(year=ExtractYear(F('date'))) \
            .values('year', 'account__title') \
            .annotate(incomes=Sum('price')) \
            .values('year', 'incomes', id=F('account__pk')) \
            .order_by('year', 'account')
