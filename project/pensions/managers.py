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

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                's_past': Decimal(),
                's_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('pension_type'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                s_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0))),
                s_fee_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='fee'),
                        default=Decimal(0))),
                s_fee_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='fee'),
                        default=Decimal(0)))
            )
            .values(
                's_past',
                's_now',
                's_fee_now',
                's_fee_past',
                title=models.F('pension_type__title'),
                id=models.F('pension_type__pk')
            )
        )


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
