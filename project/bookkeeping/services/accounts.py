from dataclasses import dataclass, field

import polars as pl

from ...accounts.models import AccountBalance


@dataclass
class AccountServiceData:
    year: int

    data: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.data = AccountBalance.objects.year(self.year)


class AccountService:
    def __init__(self, data: AccountServiceData):
        self.data = data.data

    def total_row(self) -> dict:
        if not self.data:
            return {}

        fields = [
            "past",
            "incomes",
            "expenses",
            "balance",
            "have",
            "delta",
        ]

        data = [x.__dict__ for x in self.data]

        df = pl.DataFrame(data).select([pl.col(i) for i in fields]).sum().to_dicts()

        return df[0] if df else {}


def load_service(year: int) -> dict:
    data = AccountServiceData(year)
    obj = AccountService(data)

    return {
        "items": obj.data,
        "total_row": obj.total_row(),
    }
