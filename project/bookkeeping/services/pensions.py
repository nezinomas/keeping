import itertools as it
from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from ...core.lib import utils
from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


@dataclass
class PensionServiceData:
    year: int

    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        pensions = PensionBalance.objects.year(self.year)
        savings_as_pensions = SavingBalance.objects.year(self.year).filter(saving_type__type="pensions")
        self.data = list(it.chain(savings_as_pensions, pensions))


class PensionsService:
    def __init__(self, data: PensionServiceData):
        self.data = data.data

    @property
    def total_row(self) -> dict:
        fields = [
            "past_amount",
            "past_fee",
            "per_year_incomes",
            "per_year_fee",
            "fee",
            "incomes",
            "sold",
            "sold_fee",
            "invested",
            "market_value",
            "profit_sum",
        ]
        return utils.sum_all([x.__dict__ for x in self.data], fields)


def load_service(year: int) -> dict:
    data = PensionServiceData(year)
    obj = PensionsService(data)

    return {
        "title": _("Pensions"),
        "type": "pensions",
        "items": obj.data,
        "total_row": obj.total_row,
    }