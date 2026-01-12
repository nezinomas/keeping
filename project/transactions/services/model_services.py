from typing import cast

from django.db.models import QuerySet, Value

from ...core.services.model_services import BaseModelService
from .. import managers, models


class CommonMethodsMixin:
    objects: QuerySet

    def year(self, year):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects


class TransactionModelService(
    CommonMethodsMixin, BaseModelService[managers.TransactionQuerySet]
):
    def get_queryset(self):
        return cast(managers.TransactionQuerySet, models.Transaction.objects).related(
            self.user
        )


class SavingCloseModelService(
    CommonMethodsMixin, BaseModelService[managers.SavingCloseQuerySet]
):
    objects: managers.SavingCloseQuerySet

    def get_queryset(self):
        return cast(managers.SavingCloseQuerySet, models.SavingClose.objects).related(
            self.user
        )

    def sum_by_month(self, year, month=None):
        return self.objects.month_sum(year=year, month=month).annotate(
            title=Value("savings_close")
        )


class SavingChangeModelService(
    CommonMethodsMixin, BaseModelService[managers.SavingChangeQuerySet]
):
    def get_queryset(self):
        return cast(managers.SavingChangeQuerySet, models.SavingChange.objects).related(
            self.user
        )
