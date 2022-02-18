from django.db import models
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import ExtractYear, TruncMonth

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin

class DebtQuerySet(models.QuerySet):
    def related(self):
        _journal = utils.get_user().journal
        _type = utils.get_request_kwargs('type')

        return (
            self
            .select_related('account', 'journal')
            .filter(journal=_journal, type=_type)
        )

    def items(self):
        return (
            self
            .related()
            .filter(closed=False)
        )

    def year(self, year):
        return (
            self
            .related()
            .filter(
                Q(date__year=year) | (Q(date__year__lt=year) & Q(closed=False))
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
            .aggregate(debt=Sum('price'), debt_return=Sum('returned'))
        )

    def incomes(self):
        return (
            self
            .related()
            .annotate(year=ExtractYear(F('date')))
            .values('year', 'account__title')
            .annotate(incomes=Sum('price'))
            .values('year', 'incomes', id=F('account__pk'))
            .order_by('year', 'account')
        )


class DebtReturnQuerySet(SumMixin, models.QuerySet):
    def related(self):
        _journal = utils.get_user().journal
        _type = utils.get_request_kwargs('type')

        qs = (
            self
            .select_related('account', 'debt')
            .filter(debt__journal=_journal, debt__type=_type)
        )
        return qs

    def items(self):
        return self.related().all()

    def year(self, year):
        return self.related().filter(date__year=year)

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
