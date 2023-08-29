from dataclasses import dataclass, field
from typing import Dict

from django.db.models import Sum
from django.db.models.fields import IntegerField

from ...core.lib import utils
from ...core.signals import Savings as signal_savings
from ...incomes.models import Income
from ...savings.models import Saving, SavingBalance
from .index import IndexService


@dataclass
class SavingServiceData:
    year: int

    incomes: float = field(init=False, default=0)
    savings: list = field(init=False, default_factory=list)
    total_savings: float = field(init=False, default=0)
    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        # incomes
        self.incomes = (
            Income.objects.related()
            .year(year=self.year)
            .aggregate(Sum("price", output_field=IntegerField()))["price__sum"]
        )

        self.total_savings = (
            Saving.objects.related()
            .year(self.year)
            .aggregate(Sum("price", output_field=IntegerField()))["price__sum"]
            or 0
        )

        # data
        self.data = SavingBalance.objects.year(self.year).exclude(
            saving_type__type="pensions"
        )


class SavingsService:
    def __init__(self, data: SavingServiceData):
        self.data = data.data
        self.incomes = data.incomes
        self.total_savings = data.total_savings

    def context(self) -> Dict:
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

        return {
            "items": self.data,
            "total_row": utils.sum_all(self.data, fields),
            "incomes": self.incomes,
            "savings": self.total_savings,
        }
