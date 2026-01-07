from typing import Self

from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import ExtractYear

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class ExpenseTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return (
            self.select_related("journal")
            .prefetch_related("expensename_set")
            .filter(journal=user.journal)
        )


class ExpenseNameQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("parent").filter(parent__journal=user.journal)


class ExpenseQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("expense_type", "expense_name", "account").filter(
            expense_type__journal=user.journal
        )

    def expenses(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(user)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(expenses=Sum("price"))
            .values("year", "expenses", category_id=F("account__pk"))
            .order_by("year", "category_id")
        )

    def filter_types(self, arr: list | None = None) -> Self:
        return self.filter(expense_type__in=arr) if arr else self

    def filter_names(self, arr: list | None = None) -> Self:
        return self.filter(expense_name__in=arr) if arr else self

    filter_types.queryset_only = True
    filter_names.queryset_only = True
