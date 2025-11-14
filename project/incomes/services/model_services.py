from typing import Optional, cast

from django.db.models import Count, F, Sum, Value
from django.db.models.functions import TruncMonth, TruncYear

from ...users.models import User
from .. import managers, models


class IncomeTypeModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.IncomeTypeQuerySet, models.IncomeType.objects
        ).related(user)

    def items(self):
        return self.objects.all()


class IncomeModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(managers.IncomeQuerySet, models.Income.objects).related(
            user
        )

    def year(self, year: int):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects.all()

    def sum_by_year(self, income_type: Optional[list] = None):
        qs = self.objects

        if income_type:
            qs = qs.filter(income_type__type__in=income_type)

        return qs.year_sum()

    def sum_by_month(self, year: int, month: Optional[int] = None):
        return self.objects.month_sum(year, month).annotate(title=Value("incomes"))

    def sum_by_month_and_type(self, year: int):
        return (
            self.objects.filter(date__year=year)
            .annotate(cnt=Count("income_type"))
            .values("income_type")
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(c=Count("id"))
            .annotate(sum=Sum("price"))
            .order_by("income_type__title", "date")
            .values("date", "sum", title=F("income_type__title"))
        )

    def sum_by_year_and_type(self):
        return (
            self.objects.annotate(cnt=Count("income_type"))
            .values("income_type")
            .annotate(date=TruncYear("date"))
            .values("date")
            .annotate(c=Count("id"))
            .annotate(sum=Sum("price"))
            .order_by("income_type__title", "date")
            .values("date", "sum", title=F("income_type__title"))
        )
