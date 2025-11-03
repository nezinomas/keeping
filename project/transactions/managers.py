from typing import Optional

from django.db import models
from django.db.models import F, Sum, Value
from django.db.models.functions import ExtractYear

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..journals.models import Journal


class BaseMixin(models.QuerySet):
    def related(self, journal: Optional[Journal] = None):
        #Todo: Refactore journal
        journal = journal or utils.get_user().journal
        return self.select_related("from_account", "to_account").filter(
            from_account__journal=journal, to_account__journal=journal
        )

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self):
        return self.related()

    def incomes(self, journal: Journal):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(journal)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "to_account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("to_account__pk"))
            .order_by("year", "category_id")
        )

    def annotate_fee(self, fee):
        return self.annotate(fee=Sum("fee")) if fee else self

    annotate_fee.queryset_only = True

    def base_expenses(self, journal: Journal, fee=False):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        values = ["year", "expenses"]

        if fee:
            values.append("fee")

        return (
            self.related(journal)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "from_account__title")
            .annotate(expenses=Sum("price"))
            .annotate_fee(fee=fee)
            .values(*values, category_id=F("from_account__pk"))
            .order_by("year", "category_id")
        )

    base_expenses.queryset_only = True


class TransactionQuerySet(BaseMixin):
    def expenses(self, journal: Journal):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(journal=journal)


class SavingCloseQuerySet(BaseMixin, SumMixin):
    def sum_by_month(self, year, month=None):
        return (
            self.related()
            .month_sum(year=year, month=month)
            .annotate(title=Value("savings_close"))
        )

    def expenses(self, journal: Journal):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(journal=journal, fee=True)


class SavingChangeQuerySet(BaseMixin):
    def expenses(self, journal: Journal):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(journal=journal, fee=True)
