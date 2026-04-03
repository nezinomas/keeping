from typing import cast

from django.db.models import F, QuerySet, Sum, Value
from django.db.models.functions import ExtractYear

from ...core.services.model_services import BaseModelService
from .. import managers, models


class CommonMethodsMixin:
    objects: QuerySet

    def year(self, year):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects.all()

    def incomes(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "to_account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("to_account__pk"))
            .order_by("year", "category_id")
        )

    def base_expenses(self, fee=False):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        values = ["year", "expenses"]

        if fee:
            values.append("fee")

        # Annotate the total price for each year and account
        objects = (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "from_account__title")
            .annotate(expenses=Sum("price"))
        )

        # Annotate the total fee for each year and account if fee is True
        objects = objects.annotate(fee=Sum("fee")) if fee else objects

        return objects.values(*values, category_id=F("from_account__pk")).order_by(
            "year", "category_id"
        )


class TransactionModelService(
    CommonMethodsMixin, BaseModelService[managers.TransactionQuerySet]
):
    def get_queryset(self):
        return cast(managers.TransactionQuerySet, models.Transaction.objects).related(
            self.user
        )

    def expenses(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses()


class SavingCloseModelService(
    CommonMethodsMixin, BaseModelService[managers.SavingCloseQuerySet]
):
    objects: managers.SavingCloseQuerySet

    def get_queryset(self):
        return cast(managers.SavingCloseQuerySet, models.SavingClose.objects).related(
            self.user
        )

    def sum_by_month(self, year, month=None):
        return self.objects.month_sum(year=year, month=month).annotate(
            title=Value("savings_close")
        )

    def expenses(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(fee=True)


class SavingChangeModelService(
    CommonMethodsMixin, BaseModelService[managers.SavingChangeQuerySet]
):
    def get_queryset(self):
        return cast(managers.SavingChangeQuerySet, models.SavingChange.objects).related(
            self.user
        )

    def expenses(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(fee=True)
