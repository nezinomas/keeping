from django.db import models
from django.db.models import F, Max

from ..core.lib import utils


class SavingWorthQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('saving_type')
            .filter(saving_type__user=user)
        )

    def items(self):
        qs = (
            self
            .related()
            .values('saving_type__title')
            .annotate(max_id=Max('id'))
            .order_by()
        )

        ids = [x['max_id'] for x in qs ]

        return (
            self
            .filter(pk__in=ids)
            .values(
                title=F('saving_type__title'),
                have=F('price'),
                latest_check=F('date')
            )
        )


class AccountWorthQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('account')
            .filter(account__user=user)
        )

    def items(self):
        qs = (
            self
            .related()
            .values('account__title')
            .annotate(max_id=Max('id'))
            .order_by()
        )

        ids = [x['max_id'] for x in qs]

        return (
            self
            .filter(pk__in=ids)
            .values(
                title=F('account__title'),
                have=F('price'),
                latest_check=F('date')
            )
        )


class PensionWorthQuerySet(models.QuerySet):
    def related(self):
        user = utils.get_user()
        return (
            self
            .select_related('pension_type')
            .filter(pension_type__user=user)
        )

    def items(self):
        qs = (
            self
            .related()
            .values('pension_type__title')
            .annotate(max_id=Max('id'))
            .order_by()
        )

        ids = [x['max_id'] for x in qs]

        return (
            self
            .filter(pk__in=ids)
            .values(
                title=F('pension_type__title'),
                have=F('price'),
                latest_check=F('date')
            )
        )
