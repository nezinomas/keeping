from ...accounts.services.model_services import AccountBalanceModelService
from ...users.models import User
from ..lib.total_rows import total_row


def get_data(user: User, year: int):
    return AccountBalanceModelService(user).year(year)


def load_service(user: User, year: int) -> dict:
    data = get_data(user, year)
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
