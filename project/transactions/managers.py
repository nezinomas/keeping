from decimal import Decimal
from typing import Any, Dict, List

from django.db import models
from django.db.models import Case, Count, F, Sum, When
from django.db.models.functions import ExtractYear

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class TransactionQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('from_account', 'to_account')
            .filter(from_account__journal=journal, to_account__journal=journal)
        )

    def year(self, year):
        return (
            self
            .related()
            .filter(date__year=year)
        )

    def items(self):
        return self.related()

    def summary_from(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': from_account.title,
                'tr_from_past': Decimal(),
                'tr_from_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('from_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                tr_from_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                tr_from_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values(
                'tr_from_past',
                'tr_from_now',
                title=models.F('from_account__title'))
        )

    def summary_to(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': to_account.title,
                'tr_to_past': Decimal(),
                'tr_to_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('to_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                tr_to_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                tr_to_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values(
                'tr_to_past',
                'tr_to_now',
                title=models.F('to_account__title'))
        )

    def incomes(self):
        return (
            self
            .related()
            .annotate(year=ExtractYear(F('date')))
            .values('year', 'to_account__title')
            .annotate(incomes=Sum('price'))
            .values('year', 'incomes', id=F('to_account__pk'))
            .order_by('year', 'id')
        )

    def expenses(self):
        return (
            self
            .related()
            .annotate(year=ExtractYear(F('date')))
            .values('year', 'from_account__title')
            .annotate(expenses=Sum('price'))
            .values('year', 'expenses', id=F('from_account__pk'))
            .order_by('year', 'id')
        )

class SavingCloseQuerySet(SumMixin, TransactionQuerySet):
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

    def summary_from(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': from_account.title,
                's_close_from_past': Decimal(),
                's_close_from_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('from_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_close_from_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                s_close_from_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0))),
                s_close_from_fee_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='fee'),
                        default=Decimal(0))),
                s_close_from_fee_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='fee'),
                        default=Decimal(0)))
            )
            .values(
                's_close_from_past',
                's_close_from_now',
                's_close_from_fee_past',
                's_close_from_fee_now',
                title=models.F('from_account__title'))
        )

    def summary_to(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': to_account.title,
                's_close_to_past': Decimal(),
                's_close_to_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('to_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_close_to_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                s_close_to_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0))),
            )
            .values(
                's_close_to_past',
                's_close_to_now',
                title=models.F('to_account__title'))
        )

    def incomes(self):
        return (
            self
            .related()
            .annotate(year=ExtractYear(F('date')))
            .values('year', 'to_account__title')
            .annotate(incomes=Sum('price'))
            .values('year', 'incomes', id=F('to_account__pk'))
            .order_by('year', 'id')
        )

class SavingChangeQuerySet(TransactionQuerySet):
    def summary_from(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': from_account.title,
                's_change_from_past': Decimal(),
                's_change_from_now': Decimal()
                's_change_from_fee_past': Decimal(),
                's_change_from_fee_now': Decimal(),
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('from_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_change_from_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                s_change_from_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0))),
                s_change_from_fee_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='fee'),
                        default=Decimal(0))),
                s_change_from_fee_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='fee'),
                        default=Decimal(0)))
            )
            .values(
                's_change_from_past',
                's_change_from_now',
                's_change_from_fee_past',
                's_change_from_fee_now',
                title=models.F('from_account__title'))
        )

    def summary_to(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'title': to_account.title,
                's_change_to_past': Decimal(),
                's_change_to_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('to_account'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                s_change_to_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                s_change_to_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0))),
            )
            .values(
                's_change_to_past',
                's_change_to_now',
                title=models.F('to_account__title'))
        )
