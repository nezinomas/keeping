from typing import Optional

from django.db.models import Count, F, Sum, Value
from django.db.models.functions import TruncMonth, TruncYear

from .. import managers, models
from typing import cast
from ...core.services.model_services import BaseModelService


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
        return self.objects


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
