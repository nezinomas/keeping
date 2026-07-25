from datetime import date
from functools import cached_property

from ..lib.drinks_options import DrinkConverter
from ..lib.drinks_stats import DataRow
from .model_services import DrinkModelService, DrinkTargetDTO, DrinkTargetModelService


class ConsumptionYear:
    """One user's year of drink records, in canonical Std Av units.

    The seam the Index, Risk and Trends tab modules sit on. It owns the query
    shape, the `DataRow` construction, the user's drink type, the year's target
    and the reach back into the previous year — so a tab module never touches
    the ORM or knows how a row becomes a `DataRow`.

    Every reader is cached, so asking twice costs one query.
    """

    def __init__(self, user, year: int):
        self.user = user
        self.year = year

    @cached_property
    def converter(self) -> DrinkConverter:
        return DrinkConverter(self.user.drink_type)

    @cached_property
    def daily(self) -> list[DataRow]:
        return [DataRow(**row) for row in self.daily_rows]

    @cached_property
    def monthly(self) -> list[DataRow]:
        return [DataRow(**row) for row in self._service.sum_by_month(self.year)]

    @cached_property
    def daily_rows(self) -> list[dict]:
        """The daily rows unconverted, for core modules that take dicts."""
        return list(self._service.sum_by_day(self.year))

    @cached_property
    def target(self) -> DrinkTargetDTO:
        return DrinkTargetModelService(self.user).get_target(self.year)

    @cached_property
    def last_recorded_date(self) -> date | None:
        return self._service.latest_date(self.year)

    @cached_property
    def last_recorded_date_before(self) -> date | None:
        return self._service.latest_date_before(self.year)

    @cached_property
    def previous(self) -> "ConsumptionYear":
        return ConsumptionYear(self.user, self.year - 1)

    @property
    def has_data(self) -> bool:
        return bool(self.daily_rows)

    @property
    def _service(self) -> DrinkModelService:
        return DrinkModelService(self.user)
