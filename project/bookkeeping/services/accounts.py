from project.core.lib import utils

from ...accounts.services.model_services import AccountBalanceModelService
from ...users.models import User


def load_service(user: User, year: int) -> dict:
    data = AccountBalanceModelService(user).year(year)
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
