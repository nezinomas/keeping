from typing import Optional, cast

from ...users.models import User
from ..managers import SavingBalanceQuerySet, SavingQuerySet, SavingTypeQuerySet
from ..models import Saving, SavingBalance, SavingType


class SavingTypeModelService:
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    def related(self):
        return cast(SavingTypeQuerySet, SavingType.objects).related(self.user)

    def items(self):
        return cast(SavingTypeQuerySet, SavingType.objects).items(self.user)

    def none(self):
        return SavingType.objects.none()


class SavingModelService:
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    def related(self):
        return cast(SavingQuerySet, Saving.objects).related(self.user)

    def items(self):
        return cast(SavingQuerySet, Saving.objects).items(self.user)

    def year(self, year: int):
        return cast(SavingQuerySet, Saving.objects).year(self.user, year)

    def sum_by_year(self):
        return cast(SavingQuerySet, Saving.objects).sum_by_year(self.user)

    def sum_by_month(self, year: int, month: Optional[int] = None):
        return cast(SavingQuerySet, Saving.objects).sum_by_month(self.user, year, month)

    def sum_by_month_and_type(self, year: int):
        return cast(SavingQuerySet, Saving.objects).sum_by_month_and_type(
            self.user, year
        )

    def sum_by_day_and_type(self, year: int, month: int):
        return cast(SavingQuerySet, Saving.objects).sum_by_day_and_type(
            self.user, year, month
        )

    def sum_by_day(self, year: int, month: int):
        return cast(SavingQuerySet, Saving.objects).sum_by_day(self.user, year, month)

    def last_months(self, months: int = 6):
        return cast(SavingQuerySet, Saving.objects).last_months(self.user, months)


class SavingBalanceModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    def related(self):
        return cast(SavingBalanceQuerySet, SavingBalance.objects).related(self.user)

    def items(self):
        return cast(SavingBalanceQuerySet, SavingBalance.objects).items(self.user)

    def year(self, year: int, types=None):
        return cast(SavingBalanceQuerySet, SavingBalance.objects).year(
            self.user, year, types
        )

    def sum_by_type(self):
        return cast(SavingBalanceQuerySet, SavingBalance.objects).sum_by_type(self.user)

    def sum_by_year(self):
        return cast(SavingBalanceQuerySet, SavingBalance.objects).sum_by_year(self.user)
