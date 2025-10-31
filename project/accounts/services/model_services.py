from typing import cast

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

    def related(self):
        return cast(AccountQuerySet, Account.objects).related(self.user)

    def items(self):
        return cast(AccountQuerySet, Account.objects).items(self.user, year=None)


class AccountBalanceModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    def related(self):
        return cast(AccountBalanceQuerySet, AccountBalance.objects).related(self.user)

    def items(self):
        return cast(AccountBalanceQuerySet, AccountBalance.objects).items(self.user)

    def year(self, year: int):
        return cast(AccountBalanceQuerySet, AccountBalance.objects).year(
            self.user, year
        )
