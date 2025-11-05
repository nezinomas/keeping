from typing import Optional, cast

from django.db.models import Q

from ...users.models import User
from ..managers import AccountBalanceQuerySet, AccountQuerySet
from ..models import Account, AccountBalance


class AccountModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(AccountQuerySet, Account.objects)

    def items(self, year: Optional[int] = None):
        year = year or self.user.year
        return self.model.related(self.user).filter(
            Q(closed__isnull=True) | Q(closed__gte=year)
        )

    def all(self):
        return self.model.related(self.user).all()

    def none(self):
        return Account.objects.none()


class AccountBalanceModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(AccountBalanceQuerySet, AccountBalance.objects)

    def items(self):
        return self.model.related(self.user).all()

    def year(self, year: int):
        return (
            self.model.related(self.user).filter(year=year).order_by("account__title")
        )
