from ...services.model_services import DrinkModelService
from .dtos import RiskDto


class RiskDataProvider:
    """Single point of truth for fetching risk data from the database."""

    def __init__(self, user, year: int):
        self.user = user
        self.year = year

    def get_data(self) -> RiskDto:
        service = DrinkModelService(self.user)
        return RiskDto(
            current_daily=list(service.sum_by_day(self.year)),
            past_daily=list(service.sum_by_day(self.year - 1)),
        )
