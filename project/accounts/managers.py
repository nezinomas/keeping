from django.db import models
from django.db.models import F, Q

from ..core.lib import utils


class AccountQuerySet(models.QuerySet):
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


class AccountBalanceQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        qs = (
            self
            .select_related('account')
            .filter(account__journal=journal)
        )
        return qs

    def items(self):
        return self.related()

    def year(self, year: int):
        qs = (
            self
            .related()
            .filter(year=year)
            .order_by('account__title')
        )

        return qs.values(
            'pk',
            'year',
            'past',
            'balance',
            'incomes',
            'expenses',
            'have',
            'delta',
            title=F('account__title'),
            account_pk=F('account__pk')
        )
