from ...core.lib.search import generic_search
from .model_services import IncomeModelService


def search_incomes(user, search_str):
    qs = generic_search(
        IncomeModelService(user).items(), search_str, ["income_type__title"]
    )

    return qs.values(
        "id",
        "date",
        "income_type__title",
        "account__title",
        "price",
        "remark",
    )
