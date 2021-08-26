from django.db import models
from django.db.models import F, Max

from ..core.lib import utils


class QsMixin():
    def latest_check(self, field):
        qs = (
            self
            .related()
            .values(
                title=F(f'{field}__title'),
                have=F('price'),
                latest_check=F('date')
            )
            .annotate(latest_date=Max('date'))
            .order_by('-latest_check')
        )

        rtn = []
        title = []
        for x in qs:
            if not x['title'] in title:
                rtn.append(x)
                title.append(x['title'])

        return rtn


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
