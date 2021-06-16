from decimal import Decimal
from typing import Any, Dict, List
from django.db import models
from django.db.models import Case, Count, F, Sum, When
from django.db.models.functions import ExtractYear, TruncMonth, TruncYear

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class IncomeTypeQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_journal()

        return (
            self
            .select_related('journal')
            .filter(journal=journal)
        )

    def items(self):
        return self.related()


class IncomeQuerySet(SumMixin, models.QuerySet):
    def related(self):
        journal = utils.get_journal()
        print('-----------------ef>>>>>', journal, journal)
        qs = (
            self
            .select_related('account', 'income_type')
            .filter(income_type__journal=journal)
        )
        return qs

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self):
        return self.related().all()

    def sum_by_year(self, income_type: List[str] = None):
        qs = (
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

        if income_type:
            qs = qs.filter(income_type__title__in=income_type)

        return qs

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                'i_past': Decimal(),
                'i_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('income_type'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                i_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                i_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values(
                'i_past',
                'i_now',
                title=models.F('account__title'),
                id=models.F('account__pk')
            )
        )

    def sum_by_month_and_type(self, year):
        return (
            self
            .related()
            .filter(date__year=year)
            .annotate(cnt=Count('income_type'))
            .values('income_type')
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(c=Count('id'))
            .annotate(sum=Sum('price'))
            .order_by('income_type__title', 'date')
            .values(
                'date',
                'sum',
                title=F('income_type__title'))
        )
