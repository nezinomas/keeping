import contextlib

from ...models import Drink, DrinkTarget
from ...services.model_services import DrinkModelService, DrinkTargetModelService
from .dtos import IndexDto


class IndexDataProvider:
    """Single point of truth for fetching index data from the database."""

    def __init__(self, user, year: int):
        self.user = user
        self.year = year

    def get_data(self) -> IndexDto:
        sum_by_month = DrinkModelService(self.user).sum_by_month(self.year)
        sum_by_day = DrinkModelService(self.user).sum_by_day(self.year)

        target = 0.0
        latest_past_date = None
        latest_current_date = None

        with contextlib.suppress(Drink.DoesNotExist):
            latest_past_date = (
                DrinkModelService(self.user)
                .items()
                .filter(date__year__lt=self.year)
                .latest()
                .date
            )

        with contextlib.suppress(Drink.DoesNotExist):
            latest_current_date = (
                DrinkModelService(self.user).year(self.year).latest().date
            )

        with contextlib.suppress(DrinkTarget.DoesNotExist):
            target = (
                DrinkTargetModelService(self.user)
                .year(self.year)
                .get(year=self.year)
                .qty
            )

        return IndexDto(
            sum_by_month=sum_by_month,
            sum_by_day=sum_by_day,
            target=target,
            latest_past_date=latest_past_date,
            latest_current_date=latest_current_date,
        )
