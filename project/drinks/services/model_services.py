from typing import cast

from django.db.models import F

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService
from .. import models
from ..lib.drinks_options import DrinksOptions


class DrinkModelService(SumMixin, BaseModelService):
    def get_queryset(self):
        return (
            models.Drink.objects.select_related("user")
            .filter(user=self.user)
            .order_by("-date")
        )

    def year(self, year):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects

    def sum_by_year(self, year=None) -> list[dict]:
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'stdav': float, 'qty': float}]
        """

        ratio = DrinksOptions(self.user.drink_type).ratio

        return (
            self.year_sum(
                self.objects, year=year, sum_annotation="stdav", sum_column="stdav"
            )
            .annotate(qty=F("stdav") * ratio)
            .order_by("date")
        )

    def sum_by_month(self, year: int, month: int | None = None) -> list[dict]:
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'stdav': float, 'qty': float}]
        """

        ratio = DrinksOptions(self.user.drink_type).ratio

        return (
            self.month_sum(
                self.objects,
                year=year,
                month=month,
                sum_annotation="stdav",
                sum_column="stdav",
            )
            .annotate(qty=F("stdav") * ratio)
            .order_by("date")
        )

    def sum_by_day(self, year: int, month: int | None = None) -> list[dict]:
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'stdav': float, 'qty': float}]
        """

        ratio = DrinksOptions(self.user.drink_type).ratio

        return (
            self.day_sum(
                self.objects,
                year=year,
                month=month,
                sum_annotation="stdav",
                sum_column="stdav",
            )
            .annotate(qty=F("stdav") * ratio)
            .order_by("date")
        )


class DrinkTargetModelService(BaseModelService):
    def get_queryset(self):
        return models.DrinkTarget.objects.select_related("user").filter(user=self.user)

    def year(self, year):
        obj = DrinksOptions(self.user.drink_type)
        return (
            self.objects.filter(year=year)
            .annotate(stdav=F("quantity"))
            .annotate(qty=obj.stdav_to_ml(stdav=F("stdav")))
            .annotate(max_bottles=obj.stdav_to_bottles(year, F("stdav")))
        )

    def items(self):
        return self.objects
