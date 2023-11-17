from ...accounts.models import AccountBalance
from project.core.lib import utils


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
        "total_row": utils.total_row(data, fields),
    }
