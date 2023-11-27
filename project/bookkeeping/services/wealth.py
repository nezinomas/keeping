from dataclasses import dataclass, field

from django.db.models import Model, QuerySet, Sum
from django.utils.translation import gettext as _

from ...accounts.models import AccountBalance
from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


@dataclass
class WealthServiceData:
    year: int

    account_balance: float = field(init=False, default=0)
    saving_balance: float = field(init=False, default=0)
    pension_balance: float = field(init=False, default=0)

    def __post_init__(self):
        self.account_balance = self.get_balance("balance", AccountBalance)
        self.saving_balance = self.get_balance("market_value", SavingBalance)
        self.pension_balance = self.get_balance("market_value", PensionBalance)

    def get_balance(self, field_name: str, model: Model) -> QuerySet | int:
        return (
            model.objects.related()
            .filter(year=self.year)
            .aggregate(Sum(field_name))[f"{field_name}__sum"]
            or 0
        )


@dataclass
class WealthService:
    data: WealthServiceData

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


def load_service(year: int) -> dict:
    obj = WealthService(WealthServiceData(year))

    return {
        "data": {
            "title": [_("Money"), _("Wealth")],
            "data": [obj.money, obj.wealth],
        }
    }
