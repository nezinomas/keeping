from dataclasses import dataclass, field

from ...core.lib import utils
from ...pensions.models import PensionBalance


@dataclass
class PensionServiceData:
    year: int

    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.data = PensionBalance.objects.year(self.year)


class PensionsService:
    def __init__(self, data: PensionServiceData):
        self.data = data.data

    @property
    def total_row(self) -> dict:
        fields = [
            'past_amount',
            'past_fee',
            'incomes',
            'fee',
            'invested',
            'market_value',
            'profit_incomes_sum',
            'profit_incomes_proc',
            'profit_invested_sum',
            'profit_invested_proc',
        ]

        return utils.sum_all(self.data, fields)
