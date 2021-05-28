from decimal import Decimal
from typing import Any, Dict, List

from django.db import models
from django.db.models import Case, Count, F, Sum, When

from ..core.lib import utils


class BorrowQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
            .filter(closed=False)
        )

    def items(self):
        return self.related()

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


class BorrowReturnQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        qs = (
            self
            .select_related('account', 'borrow')
            .filter(borrow__user=user)
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
        user = utils.get_user()
        return (
            self
            .select_related('user')
            .filter(user=user)
            .filter(closed=False)
        )

    def items(self):
        return self.related()

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
