from dataclasses import dataclass, field

from django.db.models import Model, Sum
from django.utils.translation import gettext as _

from ...users.models import User
from ...accounts.services.model_services import AccountBalanceModelService
from ...savings.services.model_services import SavingBalanceModelService
from ...pensions.services.model_services import PensionBalanceModelService

@dataclass
class Data:
    user: User
    year: int

    account_balance: float = field(init=False, default=0)
    saving_balance: float = field(init=False, default=0)
    pension_balance: float = field(init=False, default=0)

    def __post_init__(self):
        self.account_balance = self.get_balance("balance", AccountBalanceModelService)
        self.saving_balance = self.get_balance("market_value", SavingBalanceModelService)
        self.pension_balance = self.get_balance("market_value", PensionBalanceModelService)

    def get_balance(self, field_name: str, model: Model) -> int:
        return (
            model(self.user).year(self.year)
            .filter(year=self.year)
            .aggregate(Sum(field_name))[f"{field_name}__sum"]
            or 0
        )


@dataclass
class Wealth:
    data: Data

    @property
    def money(self):
        return 0 + self.data.account_balance + self.data.saving_balance

    @property
    def wealth(self):
        return (
            0
            + self.data.account_balance
            + self.data.saving_balance
            + self.data.pension_balance
        )


def load_service(user, year: int) -> dict:
    obj = Wealth(Data(user, year))

    return {
        "data": {
            "title": [_("Money"), _("Wealth")],
            "data": [obj.money, obj.wealth],
        }
    }
