from typing import Dict

from django.db.models import Sum

from ...core.lib.utils import sum_all
from ...incomes.models import Income
from ...savings.models import SavingBalance
from .views_helpers import add_latest_check_key
from ..models import SavingWorth
from .index import IndexService


class SavingsService:
    def __init__(self, year: int):
        self.total_incomes = self._get_total_incomes(year)
        self.savings = self._get_savings(year)

        add_latest_check_key(SavingWorth, self.savings, year)

    def _get_total_incomes(self, year: int) -> float:
        val = \
            Income.objects \
            .related() \
            .year(year=year) \
            .aggregate(Sum('price')) \
            ['price__sum']

        return float(val) if val else 0.0

    def _get_savings(self, year: int) -> Dict:
        return \
            SavingBalance.objects.year(year)

    def context(self) -> Dict:
        total_row = sum_all(self.savings)

        total_past = total_row.get('past_amount', 0)
        total_savings = total_row.get('incomes', 0)
        total_invested = total_row.get('invested', 0)
        total_market = total_row.get('market_value', 0)
        total_savings_current_year = total_savings - total_past

        calculate_percent = IndexService.percentage_from_incomes

        return {
            'items': self.savings,
            'total_row': total_row,
            'percentage_from_incomes': \
                calculate_percent(self.total_incomes, total_savings_current_year),
            'profit_incomes_proc': \
                calculate_percent(total_savings, total_market) - 100,
            'profit_invested_proc': \
                calculate_percent(total_invested, total_market) - 100,
        }
