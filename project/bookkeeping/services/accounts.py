from dataclasses import dataclass, field

from ...accounts.models import AccountBalance
from ...core.lib import utils


@dataclass
class AccountServiceData:
    year: int

    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.data = AccountBalance.objects.year(self.year)


class AccountService:
    def __init__(self, data: AccountServiceData):
        self.data = data.data

    @property
    def total_row(self) -> dict:
        total_row = {
            'past': 0,
            'incomes': 0,
            'expenses': 0,
            'balance': 0,
            'have': 0,
            'delta': 0,
        }

        for obj in self.data:
            for k in total_row:
                total_row[k] += getattr(obj, k)

        return total_row
