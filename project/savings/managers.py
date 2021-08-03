from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import Case, Count, F, Q, Sum, When
from django.db.models.functions import TruncMonth

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

    def items(self):
        user = utils.get_user()
        return (
            self
            .related()
            .filter(
                Q(closed__isnull=True) |
                Q(closed__gte=user.year)
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

    def _summary(self, year):
        return (
            self
            .related()
            .annotate(cnt=Count('saving_type'))
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
        )

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

    def summary_from(self, year: int) -> List[Dict[str, Any]]:
        '''
        summary for accounts
        return:
            {
                'title': ACCOUNT,
                's_past': Decimal(),
                's_now': Decimal()
            }
        '''
        return (
            self
            .related()
            ._summary(year)
            .values(
                's_past',
                's_now',
                title=models.F('account__title'),
            )
        )

    def summary_to(self, year: int) -> List[Dict[str, Any]]:
        '''
        summary for saving_types
        return:
            {
                'title': SAVING_TYPE,
                's_past': Decimal(),
                's_now': Decimal(),
                's_fee_past': Decimal(),
                's_free_now': Decimal()
            }
        '''
        return (
            self
            .related()
            ._summary(year)
            .values(
                's_past',
                's_now',
                's_fee_past',
                's_fee_now',
                title=models.F('saving_type__title'),
            )
        )

    def last_months(self, months: int = 6) -> float:
        # previous month
        # if today February, then start is 2020-01-31
        start = date.today().replace(day=1) - timedelta(days=1)

        # back months to past; if months=6 then end=2019-08-01
        end = (start + timedelta(days=1)) - relativedelta(months=months)

        qs = self.related().filter(date__range=(end, start)).aggregate(sum=Sum('price'))

        return qs


class SavingBalanceQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('saving_type')
            .filter(saving_type__journal=journal)
        )
        return qs

    def items(self):
        return self.related()

    def year(self, year: int):
        qs = self.related().filter(year=year)

        return qs.values(
            'year',
            'past_amount', 'past_fee',
            'fees', 'invested', 'incomes', 'market_value',
            'profit_incomes_proc', 'profit_incomes_sum',
            'profit_invested_proc', 'profit_invested_sum',
            title=F('saving_type__title')
        )
