from django.db.models import Sum

from ....accounts.services.model_services import AccountBalanceModelService
from ....core.services.model_services import BaseModelService
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
                "market_value", SavingBalanceModelService(self.user)
            ),
            pension_balance=self._get_balance(
                "market_value", PensionBalanceModelService(self.user)
            ),
        )

    def _get_balance(self, field_name: str, service: BaseModelService) -> float:
        return (
            service.year(self.year).aggregate(Sum(field_name))[f"{field_name}__sum"]
            or 0.0
        )
