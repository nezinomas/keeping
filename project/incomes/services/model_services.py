from typing import Optional

from django.db.models import Count, F, Sum, Value
from django.db.models.functions import ExtractYear, TruncMonth, TruncYear

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService
from .. import models


class IncomeTypeModelService(BaseModelService):
    def get_queryset(self):
        return models.IncomeType.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def year(self, year: int):
        raise NotImplementedError(
            "IncomeTypeModelService.year is not implemented. Use items() instead."
        )

    def items(self):
        return self.objects.all()


class IncomeModelService(SumMixin, BaseModelService):
    def get_queryset(self):
        return models.Income.objects.select_related("account", "income_type").filter(
            income_type__journal=self.user.journal
        )

    def year(self, year: int):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects.all()

    def sum_by_year(self, income_type: Optional[list] = None):
        qs = self.objects

        if income_type:
            qs = qs.filter(income_type__type__in=income_type)

        return self.year_sum(qs)

    def sum_by_month(self, year: int, month: Optional[int] = None):

        return self.month_sum(self.objects,year, month).annotate(title=Value("incomes"))

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
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "account")
        )
