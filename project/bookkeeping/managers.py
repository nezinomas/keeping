from django.db import models
from django.db.models import F, Max

from ..core.lib import utils


class QsMixin():
    def year_filter(self, year, field='date'):
        if year:
            return self.filter(**{f'{field}__year': year})

        return self

    def latest_check(self, field, year=None):
        qs = [*(
            self
            .related()
            .year_filter(year)
            .values(f'{field}_id')
            .annotate(latest_date=Max('date'))
            .order_by('-latest_date')
        )]

        dates = []
        field_id = []
        for x in qs:
            dates.append(x['latest_date'])
            field_id.append(x[f'{field}_id'])

        qs = (
            self
            .filter(**{'date__in': dates, f'{field}_id__in': field_id})
            .values(
                title=F(f'{field}__title'),
                have=F('price'),
                latest_check=F('date')
            )
        )

        return qs


class SavingWorthQuerySet(QsMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('saving_type')
            .filter(saving_type__journal=journal)
        )

    def items(self, year=None):
        return self.latest_check(field='saving_type', year=year)


class AccountWorthQuerySet(QsMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('account')
            .filter(account__journal=journal)
        )

    def items(self, year=None):
        return self.latest_check(field='account', year=year)


class PensionWorthQuerySet(QsMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('pension_type')
            .filter(pension_type__journal=journal)
        )

    def items(self, year=None):
        return self.latest_check(field='pension_type', year=year)
