from typing import Optional, cast

from django.db.models import Q

from ...core.services.model_services import BaseModelService
from .. import managers, models


class AccountModelService(BaseModelService[managers.AccountQuerySet]):
    def get_queryset(self):
        return cast(managers.AccountQuerySet, models.Account.objects).related(self.user)

    def year(self, year: int):
        return self.objects

    def items(self, year: Optional[int] = None):
        year = year or self.user.year
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))

    def all(self):
        return self.objects.all()

    def none(self):
        return models.Account.objects.none()


class AccountBalanceModelService(BaseModelService[managers.AccountBalanceQuerySet]):
    def get_queryset(self):
        return cast(
            managers.AccountBalanceQuerySet, models.AccountBalance.objects
        ).related(self.user)

    def items(self):
        return self.objects.all()

    def year(self, year: int):
        return self.objects.filter(year=year).order_by("account__title")
