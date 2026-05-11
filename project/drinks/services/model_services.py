from django.db.models import F

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService
from .. import models
from ..lib.drinks_options import DrinkConverter


class DrinkModelService(SumMixin, BaseModelService):
    def get_queryset(self):
        return (
            models.Drink.objects.select_related("user")
            .filter(user=self.user)
            .order_by("-date")
        )

    @property
    def ratio(self) -> float:
        return DrinkConverter(self.user.drink_type).ratio

    def year(self, year):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects

    def sum_by_year(self, year: int | None = None) -> list[dict]:
        """
        Returns list of dicts: [{'year': int, 'stdav': float, 'qty': float}]
        """
        return (
            self.year_sum(
                self.objects, year=year, sum_annotation="stdav", sum_column="stdav"
            ).annotate(qty=F("stdav") * self.ratio)
        )

    def sum_by_month(self, year: int, month: int | None = None) -> list[dict]:
        """
        Returns list of dicts: [{'date': datetime.date, 'stdav': float, 'qty': float}]
        """
        return (
            self.month_sum(
                self.objects,
                year=year,
                month=month,
                sum_annotation="stdav",
                sum_column="stdav",
            ).annotate(qty=F("stdav") * self.ratio)
        )

    def sum_by_day(self, year: int, month: int | None = None) -> list[dict]:
        """
        Returns list of dicts: [{'date': datetime.date, 'stdav': float, 'qty': float}]
        """
        return (
            self.day_sum(
                self.objects,
                year=year,
                month=month,
                sum_annotation="stdav",
                sum_column="stdav",
            ).annotate(qty=F("stdav") * self.ratio)
        )


class DrinkTargetModelService(BaseModelService):
    def get_queryset(self):
        return models.DrinkTarget.objects.select_related("user").filter(user=self.user)

    def year(self, year):
        converter = DrinkConverter(self.user.drink_type)
        return (
            self.objects.filter(year=year)
            .annotate(stdav=F("quantity"))
            .annotate(qty=converter.stdav_to_ml(stdav=F("stdav")))
            .annotate(max_bottles=converter.max_bottles_per_year(year, F("stdav")))
        )

    def items(self):
        return self.objects
