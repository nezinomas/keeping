from dataclasses import dataclass, field

from ...core.lib import utils
from ...core.signals import Savings as signal_savings
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
            'past_amount', 'past_fee',
            'per_year_incomes', 'per_year_fee',
            'fee', 'incomes',
            'sold', 'sold_fee',
            'invested', 'market_value',
            'profit_sum',
        ]
        total_row = utils.sum_all(self.data, fields)
        args = (total_row['market_value'], total_row['invested'])
        total_row['profit_proc'] = signal_savings.calc_percent(args)
        return total_row
