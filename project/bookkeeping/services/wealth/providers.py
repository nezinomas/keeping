from django.db.models import Sum

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

    def get_wealth_data(self, account_balance: int) -> WealthDto:
        return WealthDto(
            account_balance=account_balance,
            saving_balance=self._fresh_worth(SavingBalanceModelService(self.user)),
            pension_balance=self._fresh_worth(PensionBalanceModelService(self.user)),
        )

    def _fresh_worth(self, service: DatedModelService) -> int:
        return service.year(self.year).aggregate(
            total=Sum("market_value", filter=FRESH_WORTH, default=0)
        )["total"]
