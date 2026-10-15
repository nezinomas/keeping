from django.db.models import Q

from ...core.services.model_services import BaseModelService, DatedModelService
from .. import models


class AccountModelService(BaseModelService):
    def get_queryset(self):
        return models.Account.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def items(self):
        return self.items_in(self.user.selected_year())

    def items_in(self, year: int):
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))

    def all(self):
        return self.objects.all()

    def none(self):
        return self.objects.none()


class AccountBalanceModelService(DatedModelService):
    def get_queryset(self):
        return models.AccountBalance.objects.select_related("account").filter(
            account__journal=self.user.journal
        )

    def items(self):
        return self.objects.all()

    def year(self, year: int):
        return self.objects.filter(year=year).order_by("account__title")
