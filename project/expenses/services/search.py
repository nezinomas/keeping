from django.db.models import Count, Sum
from django.db.models.functions import Coalesce

from ...core.lib.search import generic_search
from .model_services import ExpenseModelService


def search_expenses(user, search_str):
    service = ExpenseModelService(user)
    qs = generic_search(
        service.items(), search_str, ["expense_type__title", "expense_name__title"]
    )

    return service.expenses_list(qs)


def search_totals(qs):
    totals = qs.aggregate(
        count=Count("id"),
        sum_price=Coalesce(Sum("price"), 0),
        sum_quantity=Coalesce(Sum("quantity"), 0),
    )
    totals["average"] = 0.0
    if totals["sum_quantity"]:
        totals["average"] = totals["sum_price"] / totals["sum_quantity"]

    return totals
