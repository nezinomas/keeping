import contextlib
from dataclasses import dataclass
from datetime import date

from django.db.models import F, QuerySet

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService
from .. import models
from ..lib.drink_quantity import DrinkQuantity
from ..lib.drinks_options import DrinkConverter


@dataclass(frozen=True)
class DrinkTargetDTO:
    """A year's Drink Target, in the drink type the user is currently viewing in.

    A target is stored in Std Av, so it can be re-expressed in any drink type.
    That makes this a different reading from `DrinkTarget.amount`, which is the
    volume the user actually typed, in the drink type they chose at the time.
    """

    has_data: bool = False
    target_id: int = 0
    amount: DrinkQuantity = DrinkQuantity(stdav=0.0, drink_type="stdav")
    max_bottles: float = 0.0  # servings per year, not per day

    @property
    def qty(self) -> float:
        """The daily volume, in the viewing drink type."""
        return self.amount.value


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

    def latest_date(self, year: int) -> date | None:
        """Date of the last record in `year`, or None when the year is empty."""
        with contextlib.suppress(models.Drink.DoesNotExist):
            return self.year(year).latest().date

        return None

    def latest_date_before(self, year: int) -> date | None:
        """Date of the last record in any year before `year`."""
        with contextlib.suppress(models.Drink.DoesNotExist):
            return self.objects.filter(date__year__lt=year).latest().date

        return None

    def sum_by_year(self, year: int | None = None) -> QuerySet:
        """
        Returns rows of: {'year': int, 'stdav': float, 'qty': float}
        """
        return self.year_sum(
            self.objects, year=year, sum_annotation="stdav", sum_column="stdav"
        ).annotate(qty=F("stdav") * self.ratio)

    def sum_by_month(self, year: int, month: int | None = None) -> QuerySet:
        """
        Returns rows of: {'date': datetime.date, 'stdav': float, 'qty': float}
        """
        return self.month_sum(
            self.objects,
            year=year,
            month=month,
            sum_annotation="stdav",
            sum_column="stdav",
        ).annotate(qty=F("stdav") * self.ratio)

    def sum_by_day(self, year: int, month: int | None = None) -> QuerySet:
        """
        Returns rows of: {'date': datetime.date, 'stdav': float, 'qty': float}
        """
        return self.day_sum(
            self.objects,
            year=year,
            month=month,
            sum_annotation="stdav",
            sum_column="stdav",
        ).annotate(qty=F("stdav") * self.ratio)


class DrinkTargetModelService(BaseModelService):
    def get_queryset(self):
        return models.DrinkTarget.objects.select_related("user").filter(user=self.user)

    def year(self, year):
        return self.objects.filter(year=year)

    def targets(self, year: int) -> list[DrinkTargetDTO]:
        return [self._as_dto(row, year) for row in self.year(year)]

    def get_target(self, year: int) -> DrinkTargetDTO:
        if row := self.year(year).first():
            return self._as_dto(row, year)

        return DrinkTargetDTO()

    def items(self):
        return self.objects

    def _as_dto(self, row, year: int) -> DrinkTargetDTO:
        converter = DrinkConverter(self.user.drink_type)

        return DrinkTargetDTO(
            has_data=True,
            target_id=row.id,
            amount=DrinkQuantity.from_stdav(
                row.quantity, self.user.drink_type, is_volume=True
            ),
            max_bottles=converter.max_bottles_per_year(year, row.quantity),
        )
