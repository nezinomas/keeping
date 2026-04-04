from typing import cast

from django.db.models import F, Q, Sum, Value
from django.db.models.functions import ExtractYear, TruncMonth

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService
from ...users.models import User
from .. import models


class DebtModelService(BaseModelService):
    def __init__(self, user: User, debt_type: str):
        self.debt_type = debt_type

        super().__init__(user)

    def get_queryset(self):
        return models.Debt.objects.select_related("account", "journal").filter(
            journal=self.user.journal, debt_type=self.debt_type
        )

    def items(self):
        return self.objects.all()

    def open_items(self):
        return self.objects.filter(closed=False)

    def year(self, year):
        return self.objects.filter(
            Q(date__year=year) | (Q(date__year__lt=year) & Q(closed=False))
        )

    def sum_by_month(self, year, closed=False):
        qs = self.objects if closed else self.open_items()

        return (
            qs.filter(date__year=year)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                sum_debt=Sum("price"),
                sum_return=Sum("returned"),
                title=Value(self.debt_type),
                date=F("month"),
            )
            .order_by("month")
            .values("date", "title", "sum_debt", "sum_return")
        )

    def sum_all(self):
        return self.open_items().aggregate(
            debt=Sum("price"), debt_return=Sum("returned")
        )

    def incomes(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "account")
        )

    def expenses(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(expenses=Sum("price"))
            .values("year", "expenses", category_id=F("account__pk"))
            .order_by("year", "account")
        )


class DebtReturnModelService(SumMixin, BaseModelService):
    def __init__(self, user: User, debt_type: str):
        self.debt_type = debt_type

        super().__init__(user)

    def get_queryset(self):
        return models.DebtReturn.objects.select_related("account", "debt").filter(
            debt__journal=self.user.journal, debt__debt_type=self.debt_type
        )

    def items(self):
        return self.objects.all()

    def year(self, year):
        return self.objects.filter(date__year=year)

    def sum_by_month(self, year):
        return (
            self.objects.filter(date__year=year)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                sum=Sum("price"),
                title=Value(f"{self.debt_type}_return"),
                date=F("month"),
            )
            .order_by("month")
            .values("date", "sum", "title")
        )

    def total_returned_for_debt(self, debt_return_instance):
        result = self.objects.filter(debt=debt_return_instance.debt).aggregate(
            total=Sum("price")
        )
        return result.get("total") or 0

    def incomes(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total value of lend debts for each year
        """
        return (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "category_id")
        )

    def expenses(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total value of borrow debts for each year
        """
        return (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(expenses=Sum("price"))
            .values("year", "expenses", category_id=F("account__pk"))
            .order_by("year", "category_id")
        )
