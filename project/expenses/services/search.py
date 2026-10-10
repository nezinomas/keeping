from django.db.models import Count, F, FloatField, Sum
from django.db.models.functions import Cast, Coalesce

from ...core.lib.search import generic_search
from .model_services import ExpenseModelService


def search_expenses(user, search_str):
    service = ExpenseModelService(user)
    qs = generic_search(
        service.items(), search_str, ["expense_type__title", "expense_name__title"]
    )

    return service.expenses_list(qs)


def search_totals(qs):
    totals = (
        qs.annotate(count=Count("id"))
        .values("count")
        .annotate(
            sum_price=Sum("price"),
            sum_quantity=Sum("quantity"),
        )
        .order_by("count")
        .values(
            "count",
            "sum_price",
            "sum_quantity",
            average=Coalesce(
                Cast(F("sum_price"), FloatField()) / F("sum_quantity"), 0.0
            ),
        )
    )

    return totals[0] if totals else {}
