from datetime import date
from functools import cached_property

from ...core.lib.day_stats import NoPastRecord, PastRecord
from ..lib.daily_limit import DailyLimit, NoDailyLimit
from ..lib.drinks_options import DrinkConverter
from ..lib.drinks_stats import DataRow
from .model_services import DrinkModelService, DrinkTargetDTO, DrinkTargetModelService


class ConsumptionYear:
    """One user's year of Drinks in canonical Std Av; every reader is cached."""

    def __init__(self, user, year: int, today: date):
        self.user = user
        self.year = year
        self.today = today

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
    def limit(self) -> DailyLimit | NoDailyLimit:
        """The Drink Target as a chart draws it."""
        if not self.target.qty:
            return NoDailyLimit()
        return DailyLimit(self.target.qty)

    @cached_property
    def earlier(self) -> PastRecord | NoPastRecord:
        """The last Drink before the year, so its first Gap reaches back."""
        return self._service.latest_record_before(self.year)

    @cached_property
    def latest(self) -> PastRecord | NoPastRecord:
        """The last Drink on or before today, none later than the year's end."""
        through = min(self.today, date(self.year, 12, 31))
        return self._service.latest_record(through)

    @cached_property
    def previous(self) -> "ConsumptionYear":
        return ConsumptionYear(self.user, self.year - 1, self.today)

    @property
    def has_data(self) -> bool:
        return bool(self.daily_rows)

    @property
    def _service(self) -> DrinkModelService:
        return DrinkModelService(self.user)
