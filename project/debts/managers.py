from typing import Optional

from django.db import models
from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import ExtractYear, TruncMonth

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin
from ..journals.models import Journal


class DebtQuerySet(models.QuerySet):
    def related(self, journal: Optional[Journal] = None, debt_type=None):
        #Todo: Refactore
        journal = journal or utils.get_user().journal

        if not debt_type:
            debt_type = utils.get_request_kwargs("debt_type")

        return self.select_related("account", "journal").filter(
            journal=journal, debt_type=debt_type
        )

    def items(self):
        return self.related().filter(closed=False)

    def year(self, year):
        return self.related().filter(
            Q(date__year=year) | (Q(date__year__lt=year) & Q(closed=False))
        )

    def sum_by_month(self, year, debt_type=None, closed=False):
        qs = self.related(debt_type=debt_type)

        if not closed:
            qs = qs.filter(closed=False)

        return (
            qs.filter(date__year=year)
            .annotate(cnt=Count("id"))
            .values("id")
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(sum_debt=Sum("price"))
            .annotate(sum_return=Sum("returned"))
            .annotate(title=Value(f"{debt_type}"))
            .order_by("date")
        )

    def sum_all(self, debt_type=None):
        return (
            self.related(debt_type=debt_type)
            .filter(closed=False)
            .aggregate(debt=Sum("price"), debt_return=Sum("returned"))
        )

    def incomes(self, journal: Journal):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(journal=journal, debt_type="borrow")
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "account")
        )

    def expenses(self, journal: Journal):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(journal=journal, debt_type="lend")
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(expenses=Sum("price"))
            .values("year", "expenses", category_id=F("account__pk"))
            .order_by("year", "account")
        )


class DebtReturnQuerySet(SumMixin, models.QuerySet):
    def related(self, journal: Optional[Journal] = None, debt_type=None):
        journal = journal or utils.get_user().journal

        if not debt_type:
            debt_type = utils.get_request_kwargs("debt_type")

        return self.select_related("account", "debt").filter(
            debt__journal=journal, debt__debt_type=debt_type
        )

    def items(self):
        return self.related().all()

    def year(self, year):
        return self.related().filter(date__year=year)

    def sum_by_month(self, year, debt_type=None):
        qs = self.related(debt_type=debt_type)

        return (
            qs.filter(date__year=year)
            .annotate(cnt=Count("id"))
            .values("id")
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(sum=Sum("price"))
            .annotate(title=Value(f"{debt_type}_return"))
            .order_by("date")
        )

    def incomes(self, journal: Journal):
        """
        Used only in the post_save signal.
        Calculates and returns the total value of lend debts for each year
        """
        return (
            self.related(journal=journal, debt_type="lend")
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "category_id")
        )

    def expenses(self, journal: Journal):
        """
        Used only in the post_save signal.
        Calculates and returns the total value of borrow debts for each year
        """
        return (
            self.related(journal=journal, debt_type="borrow")
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(expenses=Sum("price"))
            .values("year", "expenses", category_id=F("account__pk"))
            .order_by("year", "category_id")
        )
