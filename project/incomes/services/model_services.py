from typing import Optional, cast

from django.db.models import Count, F, Sum, Value
from django.db.models.functions import TruncMonth, TruncYear

from ...users.models import User
from ..managers import IncomeQuerySet, IncomeTypeQuerySet
from ..models import Income, IncomeType


class IncomeTypeModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(IncomeTypeQuerySet, IncomeType).objects

    def items(self):
        return self.model.related(self.user).all()


class IncomeModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(IncomeQuerySet, Income).objects

    def year(self, year: int):
        return self.model.related(self.user).filter(date__year=year)

    def items(self):
        return self.model.related(self.user).all()

    def sum_by_year(self, income_type: Optional[list] = None):
        qs = self.model.related(self.user)

        if income_type:
            qs = qs.filter(income_type__type__in=income_type)

        return qs.year_sum()

    def sum_by_month(self, year: int, month: Optional[int] = None):
        return (
            self.model.related(self.user)
            .month_sum(year, month)
            .annotate(title=Value("incomes"))
        )

    def sum_by_month_and_type(self, year: int):
        return (
            self.model.related(self.user)
            .filter(date__year=year)
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
            self.model.related(self.user)
            .annotate(cnt=Count("income_type"))
            .values("income_type")
            .annotate(date=TruncYear("date"))
            .values("date")
            .annotate(c=Count("id"))
            .annotate(sum=Sum("price"))
            .order_by("income_type__title", "date")
            .values("date", "sum", title=F("income_type__title"))
        )
