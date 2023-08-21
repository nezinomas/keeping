from dataclasses import dataclass, field
from typing import Dict

from django.db.models import Sum
from django.db.models.fields import IntegerField

from ...core.lib import utils
from ...core.signals import Savings as signal_savings
from ...incomes.models import Income
from ...savings.models import SavingBalance
from .index import IndexService


@dataclass
class SavingServiceData:
    year: int

    incomes: float = field(init=False, default=0)
    savings: list = field(init=False, default_factory=list)
    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        # incomes
        self.incomes = (
            Income.objects.related()
            .year(year=self.year)
            .aggregate(Sum("price", output_field=IntegerField()))["price__sum"]
        )

        # data
        self.data = SavingBalance.objects.year(self.year).exclude(saving_type__type = 'pensions')


class SavingsService:
    def __init__(self, data: SavingServiceData):
        self.data = data.data
        self.incomes = data.incomes

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
        total_row = utils.sum_all(self.data, fields)
        total_row["profit_proc"] = signal_savings.calc_percent(
            total_row.get("market_value", 0), total_row.get("invested", 0)
        )

        total_past = total_row.get("past_amount", 0)
        total_savings = total_row.get("incomes", 0)
        total_savings_current_year = total_savings - total_past

        calculate_percent = IndexService.percentage_from_incomes

        return {
            "items": self.data,
            "total_row": total_row,
            "percentage_from_incomes": calculate_percent(
                self.incomes, total_savings_current_year
            ),
        }
