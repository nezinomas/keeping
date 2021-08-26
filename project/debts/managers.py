from decimal import Decimal
from typing import Any, Dict, List

from django.db import models
from django.db.models import Case, Count, Q, Sum, When
from django.db.models.functions import TruncMonth

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class BorrowQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('account', 'journal')
            .filter(journal=journal)
        )

    def items(self):
        return self.related()

    def year(self, year):
        return (
            self
            .related()
            .filter(
                Q(date__year=year) | (Q(date__year__lt=year) & Q(closed=False))
            )
        )

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                'borrow_past': Decimal(),
                'borrow_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('name'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                borrow_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                borrow_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values(
                'borrow_past',
                'borrow_now',
                title=models.F('account__title'),
                id=models.F('account__pk')
            )
        )

    def sum_by_month(self, year):
        return (
            self
            .related()
            .filter(closed=False)
            .filter()
            .filter(date__year=year)
            .annotate(cnt=Count('id'))
            .values('id')
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(sum_debt=Sum('price'))
            .annotate(sum_return=Sum('returned'))
            .order_by('date')
        )

    def sum_all(self):
        return (
            self
            .related()
            .filter(closed=False)
            .aggregate(borrow=Sum('price'), borrow_return=Sum('returned'))
        )


class BorrowReturnQuerySet(SumMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('account', 'borrow')
            .filter(borrow__journal=journal)
        )
        return qs

    def items(self):
        return self.related().all()

    def year(self, year):
        return self.related().filter(date__year=year)

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                'borrow_past': Decimal(),
                'borrow_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('date'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                borrow_return_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                borrow_return_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values(
                'borrow_return_past',
                'borrow_return_now',
                title=models.F('account__title'),
                id=models.F('account__pk')
            )
        )


class LentQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('account', 'journal')
            .filter(journal=journal)
        )

    def items(self):
        return self.related()

    def year(self, year):
        return (
            self
            .related()
            .filter(
                Q(date__year=year) | (Q(date__year__lt=year) & Q(closed=False))
            )
        )

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                'lent_past': Decimal(),
                'lent_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('name'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                lent_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                lent_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values(
                'lent_past',
                'lent_now',
                title=models.F('account__title'),
                id=models.F('account__pk')
            )
        )

    def sum_by_month(self, year):
        return (
            self
            .related()
            .filter(closed=False)
            .filter()
            .filter(date__year=year)
            .annotate(cnt=Count('id'))
            .values('id')
            .annotate(date=TruncMonth('date'))
            .values('date')
            .annotate(sum_debt=Sum('price'))
            .annotate(sum_return=Sum('returned'))
            .order_by('date')
        )

    def sum_all(self):
        return (
            self
            .related()
            .filter(closed=False)
            .aggregate(lent=Sum('price'), lent_return=Sum('returned'))
        )

class LentReturnQuerySet(SumMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('account', 'lent')
            .filter(lent__journal=journal)
        )
        return qs

    def items(self):
        return self.related().all()

    def year(self, year):
        return self.related().filter(date__year=year)

    def summary(self, year: int) -> List[Dict[str, Any]]:
        '''
        return:
            {
                'id': account.id,
                'title': account.title,
                'lent_past': Decimal(),
                'lent_now': Decimal()
            }
        '''
        return (
            self
            .related()
            .annotate(cnt=Count('date'))
            .values('cnt')
            .order_by('cnt')
            .annotate(
                lent_return_past=Sum(
                    Case(
                        When(**{'date__year__lt': year}, then='price'),
                        default=Decimal(0))),
                lent_return_now=Sum(
                    Case(
                        When(**{'date__year': year}, then='price'),
                        default=Decimal(0)))
            )
            .values(
                'lent_return_past',
                'lent_return_now',
                title=models.F('account__title'),
                id=models.F('account__pk')
            )
        )
