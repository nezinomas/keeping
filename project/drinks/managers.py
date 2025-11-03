from typing import Optional

from django.db import models
from django.db.models import F

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User
from .lib.drinks_options import DrinksOptions


class DrinkQuerySet(SumMixin, models.QuerySet):
    def related(self, user: Optional[User] = None):
        #Todo: Refactore User
        user = user or utils.get_user()
        return (
            self.select_related("user").filter(user=user).order_by("-date")
        )

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self):
        return self.related()

    def sum_by_year(self, year=None) -> list[dict]:
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'stdav': float, 'qty': float}]
        """

        ratio = DrinksOptions().ratio

        return (
            self.related()
            .year_sum(year=year, sum_annotation="stdav", sum_column="quantity")
            .annotate(qty=F("stdav") * ratio)
            .order_by("date")
        )

    def sum_by_month(self, year: int, month: int = None) -> list[dict]:
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'stdav': float, 'qty': float}]
        """

        ratio = DrinksOptions().ratio

        return (
            self.related()
            .month_sum(
                year=year, month=month, sum_annotation="stdav", sum_column="quantity"
            )
            .annotate(qty=F("stdav") * ratio)
            .order_by("date")
        )

    def sum_by_day(self, year: int, month: int = None) -> list[dict]:
        """
        Returns
        DrinkQuerySet [{'date': datetime.date, 'stdav': float, 'qty': float}]
        """

        ratio = DrinksOptions().ratio

        return (
            self.related()
            .day_sum(
                year=year, month=month, sum_annotation="stdav", sum_column="quantity"
            )
            .annotate(qty=F("stdav") * ratio)
            .order_by("date")
        )


class DrinkTargetQuerySet(SumMixin, models.QuerySet):
    def related(self, user: Optional[User] = None):
        #Todo: Refactore User
        user = user or utils.get_user()
        return self.select_related("user").filter(user=user)

    def year(self, year):
        obj = DrinksOptions()
        return (
            self.related()
            .filter(year=year)
            .annotate(stdav=F("quantity"))
            .annotate(qty=obj.stdav_to_ml(stdav=F("stdav")))
            .annotate(max_bottles=obj.stdav_to_bottles(year, F("stdav")))
        )

    def items(self):
        return self.related()
