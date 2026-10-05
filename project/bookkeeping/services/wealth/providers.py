from django.db.models import Q, Sum

from ....accounts.services.model_services import AccountBalanceModelService
from ....core.mixins.shows_profit import FRESH_WORTH
from ....core.services.model_services import DatedModelService
from ....pensions.services.model_services import PensionBalanceModelService
from ....savings.services.model_services import SavingBalanceModelService
from ....users.models import User
from .dtos import WealthDto


class WealthDataProvider:
    def __init__(self, user: User, year: int):
        self.user = user
        self.year = year

    def get_wealth_data(self) -> WealthDto:
        return WealthDto(
            account_balance=self._get_balance(
                "balance", AccountBalanceModelService(self.user)
            ),
            saving_balance=self._get_balance(
                "market_value", SavingBalanceModelService(self.user), FRESH_WORTH
            ),
            pension_balance=self._get_balance(
                "market_value", PensionBalanceModelService(self.user), FRESH_WORTH
            ),
        )

    def _get_balance(
        self, field_name: str, service: DatedModelService, only: Q = Q()
    ) -> float:
        return service.year(self.year).aggregate(
            total=Sum(field_name, filter=only, default=0)
        )["total"]
