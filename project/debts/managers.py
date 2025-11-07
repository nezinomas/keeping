from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import ExtractYear

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class DebtQuerySet(models.QuerySet):
    def related(self, user: User, debt_type: str):
        return self.select_related("account", "journal").filter(
            journal=user.journal, debt_type=debt_type
        )

    def incomes(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(user, debt_type="borrow")
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "account")
        )

    def expenses(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(user, debt_type="lend")
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(expenses=Sum("price"))
            .values("year", "expenses", category_id=F("account__pk"))
            .order_by("year", "account")
        )


class DebtReturnQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User, debt_type: str):
        return self.select_related("account", "debt").filter(
            debt__journal=user.journal, debt__debt_type=debt_type
        )

    def incomes(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total value of lend debts for each year
        """
        return (
            self.related(user, debt_type="lend")
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "category_id")
        )

    def expenses(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total value of borrow debts for each year
        """
        return (
            self.related(user, debt_type="borrow")
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(expenses=Sum("price"))
            .values("year", "expenses", category_id=F("account__pk"))
            .order_by("year", "category_id")
        )
