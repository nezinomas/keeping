from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import ExtractYear

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class BaseMixin(models.QuerySet):
    def related(self, user: User):
        return self.select_related("from_account", "to_account").filter(
            from_account__journal=user.journal, to_account__journal=user.journal
        )

    def incomes(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(user)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "to_account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("to_account__pk"))
            .order_by("year", "category_id")
        )

    def annotate_fee(self, fee):
        return self.annotate(fee=Sum("fee")) if fee else self

    annotate_fee.queryset_only = True

    def base_expenses(self, user: User, fee=False):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        values = ["year", "expenses"]

        if fee:
            values.append("fee")

        return (
            self.related(user)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "from_account__title")
            .annotate(expenses=Sum("price"))
            .annotate_fee(fee=fee)
            .values(*values, category_id=F("from_account__pk"))
            .order_by("year", "category_id")
        )

    base_expenses.queryset_only = True


class TransactionQuerySet(BaseMixin):
    def expenses(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(user)


class SavingCloseQuerySet(BaseMixin, SumMixin):
    def expenses(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(user, fee=True)


class SavingChangeQuerySet(BaseMixin):
    def expenses(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(user, fee=True)
