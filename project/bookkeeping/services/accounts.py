from ...accounts.models import AccountBalance
from ...core.lib.utils import total_row


def get_data(year: int) -> AccountBalance:
    return AccountBalance.objects.year(year)


def load_service(year: int) -> dict:
    data = get_data(year)
    fields = [
        "past",
        "incomes",
        "expenses",
        "balance",
        "have",
        "delta",
    ]

    return {
        "items": data,
        "total_row": total_row(data, fields),
    }
