from typing import Dict, List

from ...pensions.models import PensionBalance
from ...core.lib.utils import sum_all
from ..models import PensionWorth
from ..services.common import add_latest_check_key


class PensionsService:
    def __init__(self, year: int):
        self._data = self._get_data(year)

        add_latest_check_key(PensionWorth, self._data, year)

    def _get_data(self, year: int) -> List[Dict]:
        return PensionBalance.objects.year(year)

    @property
    def data(self) -> List[Dict]:
        return self._data

    @property
    def total_row(self) -> Dict:
        total_row = {
            'past_amount': 0,
            'past_fee': 0,
            'incomes': 0,
            'fee': 0,
            'invested': 0,
            'market_value': 0,
            'profit_incomes_sum': 0,
            'profit_incomes_proc': 0,
            'profit_invested_sum': 0,
            'profit_invested_proc': 0,
        }

        if self._data:
            total_row = sum_all(self.data)

        return total_row
