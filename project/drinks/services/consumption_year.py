from datetime import date
from functools import cached_property

from ...core.lib.day_stats import NoPastRecord, PastRecord
from ..lib.drinks_options import DrinkConverter
from ..lib.drinks_stats import DataRow
from .model_services import DrinkModelService, DrinkTargetDTO, DrinkTargetModelService


class ConsumptionYear:
    """One user's year of Drinks in canonical Std Av; every reader is cached."""

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
    def earlier(self) -> PastRecord | NoPastRecord:
        """The last Drink before the year, so its first Gap reaches back."""
        latest = self._service.latest_date_before(self.year)
        if latest is None:
            return NoPastRecord()

        return PastRecord(latest)

    @cached_property
    def latest(self) -> PastRecord | NoPastRecord:
        """The last Drink on or before today, none later than the year's end."""
        through = min(date.today(), date(self.year, 12, 31))
        latest = self._service.latest_date(through)
        if latest is None:
            return NoPastRecord()

        return PastRecord(latest)

    @cached_property
    def previous(self) -> "ConsumptionYear":
        return ConsumptionYear(self.user, self.year - 1)

    @property
    def has_data(self) -> bool:
        return bool(self.daily_rows)

    @property
    def _service(self) -> DrinkModelService:
        return DrinkModelService(self.user)
