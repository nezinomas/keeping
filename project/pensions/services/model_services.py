from typing import cast

from django.db.models import F, Sum

from ...users.models import User
from ..managers import PensionBalanceQuerySet, PensionQuerySet, PensionTypeQuerySet
from ..models import Pension, PensionBalance, PensionType


class PensionTypeModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(PensionTypeQuerySet, PensionType.objects)

    def items(self):
        return self.model.related(self.user).all()


class PensionModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(PensionQuerySet, Pension.objects)

    def year(self, year: int):
        return self.model.related(self.user).filter(date__year=year)

    def items(self):
        return self.model.related(self.user).all()


class PensionBalanceModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(PensionBalanceQuerySet, PensionBalance.objects)

    def year(self, year: int):
        return self.model.related(self.user).filter(year=year)

    def items(self):
        return self.model.related(self.user).all()

    def sum_by_year(self):
        return (
            self.model.related(self.user)
            .annotate(y=F("year"))
            .values("y")
            .annotate(incomes=Sum("incomes"), profit=Sum("profit_sum"), fee=Sum("fee"))
            .order_by("year")
            .values("year", "incomes", "profit", "fee")
        )