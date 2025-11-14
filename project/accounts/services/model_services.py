from typing import Optional, cast

from django.db.models import Q

from ...users.models import User
from .. import managers, models


class AccountModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.objects = cast(managers.AccountQuerySet, models.Account.objects).related(
            self.user
        )

    def items(self, year: Optional[int] = None):
        year = year or self.user.year
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))

    def all(self):
        return self.objects.all()

    def none(self):
        return models.Account.objects.none()


class AccountBalanceModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.AccountBalanceQuerySet, models.AccountBalance.objects
        ).related(user)

    def items(self):
        return self.objects.all()

    def year(self, year: int):
        return self.objects.filter(year=year).order_by("account__title")
