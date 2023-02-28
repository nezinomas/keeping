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
        fields = [
            "past",
            "incomes",
            "expenses",
            "balance",
            "have",
            "delta",
        ]

        return utils.sum_all(self.data, fields)
