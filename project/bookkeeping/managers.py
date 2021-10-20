from django.db import models
from django.db.models import F, Max

from ..core.lib import utils


class QsMixin():
    def latest_check(self, field):
        qs = [*(
            self
            .related()
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

    def items(self):
        return self.latest_check('saving_type')


class AccountWorthQuerySet(QsMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('account')
            .filter(account__journal=journal)
        )

    def items(self):
        return self.latest_check('account')


class PensionWorthQuerySet(QsMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return (
            self
            .select_related('pension_type')
            .filter(pension_type__journal=journal)
        )

    def items(self):
        return self.latest_check('pension_type')
