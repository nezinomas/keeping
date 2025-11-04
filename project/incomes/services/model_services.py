from typing import cast, Optional

from ...users.models import User
from ..managers import IncomeQuerySet, IncomeTypeQuerySet
from ..models import Income, IncomeType


class IncomeTypeModelService:
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
        return cast(IncomeTypeQuerySet, IncomeType.objects).related(self.user)

    def items(self):
        return cast(IncomeTypeQuerySet, IncomeType.objects).items(self.user)


class IncomeModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user

    def related(self):
        return cast(IncomeQuerySet, Income.objects).related(self.user)

    def items(self):
        return cast(IncomeQuerySet, Income.objects).items(self.user)

    def year(self, year: int):
        return cast(IncomeQuerySet, Income.objects).year(self.user, year)

    def none(self):
        return Income.objects.none()

    def sum_by_year(self, income_type: Optional[list] = None):
        return cast(IncomeQuerySet, Income.objects).sum_by_year(self.user, income_type)

    def sum_by_month(self, year: int, month: Optional[int] = None):
        return cast(IncomeQuerySet, Income.objects).sum_by_month(self.user, year, month)

    def sum_by_month_and_type(self, year: int):
        return cast(IncomeQuerySet, Income.objects).sum_by_month_and_type(
            self.user, year
        )

    def sum_by_year_and_type(self):
        return cast(IncomeQuerySet, Income.objects).sum_by_year_and_type(self.user)
