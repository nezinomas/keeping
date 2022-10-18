from typing import Dict, List

from ...accounts.models import AccountBalance
from ...core.lib.utils import sum_all
from ..models import AccountWorth
from ..services.common import add_latest_check_key


class AccountService:
    def __init__(self, year: int):
        self._data = self._get_data(year)

        add_latest_check_key(AccountWorth, self._data, year)

    def _get_data(self, year: int) -> List[Dict]:
        return AccountBalance.objects.year(year)

    @property
    def data(self) -> List[Dict]:
        return self._data

    @property
    def total_row(self) -> Dict:
        total_row = {
            'past': 0,
            'incomes': 0,
            'expenses': 0,
            'balance': 0,
            'have': 0,
            'delta': 0,
        }

        return \
            sum_all(self.data) if self._data else total_row
