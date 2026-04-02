from typing import Optional, cast

from django.db.models import Count, F, Sum, Value
from django.db.models.functions import ExtractYear, TruncMonth, TruncYear

from ...core.services.model_services import BaseModelService
from .. import managers, models


class IncomeTypeModelService(BaseModelService[managers.IncomeTypeQuerySet]):
    def get_queryset(self):
        return cast(managers.IncomeTypeQuerySet, models.IncomeType.objects).related(
            self.user
        )

    def year(self, year: int):
        raise NotImplementedError(
            "IncomeTypeModelService.year is not implemented. Use items() instead."
        )

    def items(self):
        return self.objects.all()


class IncomeModelService(BaseModelService[managers.IncomeQuerySet]):
    def get_queryset(self):
        return cast(managers.IncomeQuerySet, models.Income.objects).related(self.user)

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
            .annotate(month=TruncMonth("date"))
            .values("month", "income_type")
            .annotate(
                sum=Sum("price"),
                title=F("income_type__title"),
                date=F("month"),
            )
            .order_by("income_type__title", "date")
            .values("date", "sum", "title")
        )

    def sum_by_year_and_type(self):
        return (
            self.objects.annotate(cnt=Count("income_type"))
            .annotate(year=TruncYear("date"))
            .values("year", "income_type")
            .annotate(
                sum=Sum("price"),
                title=F("income_type__title"),
                date=F("year"),
            )
            .order_by("income_type__title", "date")
            .values("date", "sum", "title")
        )

    def incomes(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.objects
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "account")
        )
