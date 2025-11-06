from typing import cast

from django.db.models import F, Sum

from ...users.models import User
from .. import models, managers


class PensionTypeModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.PensionTypeQuerySet, models.PensionType.objects
        ).related(user)

    def items(self):
        return self.objects.all()


class PensionModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(managers.PensionQuerySet, models.Pension.objects).related(
            user
        )

    def year(self, year: int):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects.all()


class PensionBalanceModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.PensionBalanceQuerySet, models.PensionBalance.objects
        ).related(user)

    def year(self, year: int):
        return self.objects.filter(year=year)

    def items(self):
        return self.objects.all()

    def sum_by_year(self):
        return (
            self.objects.annotate(y=F("year"))
            .values("y")
            .annotate(incomes=Sum("incomes"), profit=Sum("profit_sum"), fee=Sum("fee"))
            .order_by("year")
            .values("year", "incomes", "profit", "fee")
        )
