from project.core.lib import utils

from ...accounts.services.model_services import AccountBalanceModelService
from ...users.models import User


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
        "total_row": utils.total_row(data, fields),
    }
