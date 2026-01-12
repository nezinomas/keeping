from typing import cast

from django.db.models import F, Sum

from .. import managers, models
from ...core.services.model_services import BaseModelService


class PensionTypeModelService(BaseModelService[managers.PensionTypeQuerySet]):
    def get_queryset(self):
        return cast(managers.PensionTypeQuerySet, models.PensionType.objects).related(
            self.user
        )

    def year(self, year: int):
        return self.objects

    def items(self):
        return self.objects


class PensionModelService(BaseModelService[managers.PensionQuerySet]):
    def get_queryset(self):
        return cast(managers.PensionQuerySet, models.Pension.objects).related(self.user)

    def year(self, year: int):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects.all()


class PensionBalanceModelService(BaseModelService[managers.PensionBalanceQuerySet]):
    def get_queryset(self):
        return cast(
            managers.PensionBalanceQuerySet, models.PensionBalance.objects
        ).related(self.user)

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
