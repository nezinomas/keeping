from typing import List, Optional

from django.db import models
from django.db.models import Count, F, Sum, Value
from django.db.models.functions import ExtractYear, TruncMonth, TruncYear

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class IncomeTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("journal").filter(journal=user.journal)

    def items(self, user: User):
        return self.related(user)


class IncomeQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("account", "income_type").filter(
            income_type__journal=user.journal
        )

    def year(self, user: User, year: int):
        return self.related(user).filter(date__year=year)

    def items(self, user: User):
        return self.related(user).all()

    def sum_by_year(self, user: User, income_type: Optional[list] = None):
        qs = self.related(user)

        if income_type:
            qs = qs.filter(income_type__type__in=income_type)

        return qs.year_sum()

    def sum_by_month(self, user: User, year: int, month: Optional[int] = None):
        return (
            self.related(user).month_sum(year, month).annotate(title=Value("incomes"))
        )

    def sum_by_month_and_type(self, user: User, year):
        return (
            self.related(user)
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

    def sum_by_year_and_type(self, user: User):
        return (
            self.related(user)
            .annotate(cnt=Count("income_type"))
            .values("income_type")
            .annotate(date=TruncYear("date"))
            .values("date")
            .annotate(c=Count("id"))
            .annotate(sum=Sum("price"))
            .order_by("income_type__title", "date")
            .values("date", "sum", title=F("income_type__title"))
        )

    def incomes(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(user)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "account")
        )
