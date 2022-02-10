from decimal import Decimal
from typing import Any, Dict, List

from django.db import models
from django.db.models import Case, Count, F, Sum, When

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class PensionTypeQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('journal')
            .filter(journal=journal)
        )

    def items(self, year: int = None):
        return self.related()


class PensionQuerySet(SumMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('pension_type')
            .filter(pension_type__journal=journal)
        )
        return qs

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self):
        return self.related().all()

class PensionBalanceQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('pension_type')
            .filter(pension_type__journal=journal)
        )
        return qs

    def items(self):
        return self.related()

    def year(self, year: int):
        qs = self.related().filter(year=year)

        return qs.values(
            'year',
            'past_amount',
            'past_fee',
            'fees',
            'invested',
            'incomes',
            'market_value',
            'profit_incomes_proc',
            'profit_incomes_sum',
            'profit_invested_proc',
            'profit_invested_sum',
            title=F('pension_type__title')
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
