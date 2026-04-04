from typing import Optional, cast

from django.db.models import Q

from ...core.services.model_services import BaseModelService
from .. import models


class AccountModelService(BaseModelService):
    def get_queryset(self):
        return models.Account.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def year(self, year: int):
        raise NotImplementedError(
            "AccountModelService.year is not implemented. Use items() instead."
        )

    def items(self, year: Optional[int] = None):
        year = year or self.user.year
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))

    def all(self):
        return self.objects.all()

    def none(self):
        return self.objects.none()


class AccountBalanceModelService(BaseModelService):
    def get_queryset(self):
        return models.AccountBalance.objects.select_related("account").filter(
            account__journal=self.user.journal
        )

    def items(self):
        return self.objects.all()

    def year(self, year: int):
        return self.objects.filter(year=year).order_by("account__title")
