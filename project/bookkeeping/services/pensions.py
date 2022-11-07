from dataclasses import dataclass, field

from ...core.lib.utils import sum_all
from ...pensions.models import PensionBalance
from ..models import PensionWorth
from ..services.common import add_latest_check_key


@dataclass
class PensionServiceData:
    year: int

    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        # data
        balance_data = PensionBalance.objects.year(self.year)
        worth_data = PensionWorth.objects.items(self.year)

        self.data = add_latest_check_key(worth_data, balance_data)


class PensionsService:
    def __init__(self, data: PensionServiceData):
        self.data = data.data

    @property
    def total_row(self) -> dict:
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

        return sum_all(self.data) if self.data else total_row
