from functools import reduce
from operator import or_

from django.db import models
from django.db.models import Count, F, Max, Q
from django.db.models.functions import ExtractYear

from ..core.lib import utils


class QsMixin():
    def filter_by_year(self, year):
        if year:
            return self.filter(**{'date__year__gte': (year - 1), 'date__year__lte': year})
        return self

    def latest_check(self, field, year=None):
        qs = [*(
            self
            .related()
            .filter_by_year(year)
            .values(f'{field}_id')
            .annotate(latest_date=Max('date'))
            .order_by('-latest_date')
        )]

        items = []
        for x in qs:
            items.append(
                Q(date=x['latest_date'])
                & Q(**{f'{field}_id': x[f'{field}_id']})
            )

        if not items:
            return None

        qs = (
            self
            .filter(reduce(or_, items))
            .values(
                title=F(f'{field}__title'),
                have=F('price'),
                latest_check=F('date')
            )
        )

        return qs

    def latest_have(self, field):
        qs = [*(
            self
            .related()
            .annotate(year=ExtractYear(F('date')))
            .values('year', f'{field}_id')
            .annotate(latest_date=Max('date'))
            .order_by('year')
        )]

        items = []
        for x in qs:
            items.append(
                Q(date=x['latest_date'])
                & Q(**{f'{field}_id': x[f'{field}_id']})
            )

        if not items:
            return None

        qs = (
            self
            .filter(reduce(or_, items))
            .annotate(c=Count('id'))
            .values('c')
            .annotate(year=ExtractYear(F('date')))
            .values(
                'year',
                id=F(f'{field}__id'),
                have=F('price'),
            )
        )

        return qs


class SavingWorthQuerySet(QsMixin, models.QuerySet):
    def filter_created_and_closed(self, year):
        if year:
            return self.filter(
                Q(saving_type__closed__isnull=True) |
                Q(saving_type__closed__gte=year) &
                Q(saving_type__created__year__lte=year)
            )

        return self

    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('saving_type')
            .filter(saving_type__journal=journal)
        )

    def items(self, year=None):
        return (
            self
            .filter_created_and_closed(year)
            .latest_check(field='saving_type', year=year)
        )

    def have(self):
        return (
            self
            .latest_have(field='saving_type')
        )

class AccountWorthQuerySet(QsMixin, models.QuerySet):
    def filter_created_and_closed(self, year):
        if year:
            return self.filter(
                Q(account__closed__isnull=True) |
                Q(account__closed__gte=year) &
                Q(account__created__year__lte=year)
            )

        return self

    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('account')
            .filter(account__journal=journal)
        )

    def items(self, year=None):
        return (
            self
            .filter_created_and_closed(year)
            .latest_check(field='account', year=year)
        )

    def have(self):
        return (
            self
            .latest_have(field='account')
        )


class PensionWorthQuerySet(QsMixin, models.QuerySet):
    def filter_created(self, year):
        if year:
            return self.filter(
                Q(pension_type__created__year__lte=year)
            )

        return self

    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('pension_type')
            .filter(pension_type__journal=journal)
        )

    def items(self, year=None):
        return (
            self
            .filter_created(year)
            .latest_check(field='pension_type', year=year)
        )

    def have(self):
        return (
            self
            .latest_have(field='pension_type')
        )
