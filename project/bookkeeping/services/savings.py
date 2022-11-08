from dataclasses import dataclass, field
from typing import Dict

from django.db.models import Sum
from django.db.models.fields import FloatField

from ...core.lib import utils
from ...incomes.models import Income
from ...savings.models import SavingBalance
from ..models import SavingWorth
from . import common
from .index import IndexService


@dataclass
class SavingServiceData:
    year: int

    incomes: float = field(init=False, default=0.0)
    savings: list = field(init=False, default_factory=list)
    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        # incomes
        self.incomes = \
            Income.objects \
            .related() \
            .year(year=self.year) \
            .aggregate(Sum('price', output_field=FloatField())) \
            ['price__sum']

        # data
        balance_data = SavingBalance.objects.year(self.year)
        worth_data = SavingWorth.objects.items(self.year)

        self.data = common.add_latest_check_key(worth_data, balance_data)


class SavingsService:
    def __init__(self, data: SavingServiceData):
        self.data = data.data
        self.incomes = data.incomes

    def context(self) -> Dict:
        total_row = utils.sum_all(self.data)

        total_past = total_row.get('past_amount', 0)
        total_savings = total_row.get('incomes', 0)
        total_invested = total_row.get('invested', 0)
        total_market = total_row.get('market_value', 0)
        total_savings_current_year = total_savings - total_past

        calculate_percent = IndexService.percentage_from_incomes

        return {
            'items': self.data,
            'total_row': total_row,
            'percentage_from_incomes': \
                calculate_percent(self.incomes, total_savings_current_year),
            'profit_incomes_proc': \
                calculate_percent(total_savings, total_market) - 100,
            'profit_invested_proc': \
                calculate_percent(total_invested, total_market) - 100,
        }
