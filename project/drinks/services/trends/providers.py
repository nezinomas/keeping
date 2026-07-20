import contextlib

from ...models import DrinkTarget
from ...services.model_services import DrinkModelService, DrinkTargetModelService
from .dtos import TrendsDto


class TrendsDataProvider:
    """Single point of truth for fetching trend data from the database."""

    def __init__(self, user, year: int):
        self.user = user
        self.year = year

    def get_data(self) -> TrendsDto:
        service = DrinkModelService(self.user)
        current_daily = list(service.sum_by_day(self.year))
        past_daily = list(service.sum_by_day(self.year - 1))

        target = 0.0
        with contextlib.suppress(DrinkTarget.DoesNotExist):
            target = (
                DrinkTargetModelService(self.user)
                .year(self.year)
                .get(year=self.year)
                .qty
            )

        return TrendsDto(
            current_daily=current_daily,
            past_daily=past_daily,
            target=target,
        )
