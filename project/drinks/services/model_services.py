from typing import cast

from django.db.models import F

from ...core.services.model_services import BaseModelService
from .. import managers, models
from ..lib.drinks_options import DrinksOptions


class DrinkModelService(BaseModelService[managers.DrinkQuerySet]):
    def get_queryset(self):
        return cast(managers.DrinkQuerySet, models.Drink.objects).related(self.user)

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
            self.objects.year_sum(
                year=year, sum_annotation="stdav", sum_column="quantity"
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
            self.objects.month_sum(
                year=year, month=month, sum_annotation="stdav", sum_column="quantity"
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
            self.objects.day_sum(
                year=year, month=month, sum_annotation="stdav", sum_column="quantity"
            )
            .annotate(qty=F("stdav") * ratio)
            .order_by("date")
        )


class DrinkTargetModelService(BaseModelService[managers.DrinkTargetQuerySet]):
    def get_queryset(self):
        return cast(managers.DrinkTargetQuerySet, models.DrinkTarget.objects).related(
            self.user
        )

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
