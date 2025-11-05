from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import ExtractYear

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class IncomeTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("journal").filter(journal=user.journal)


class IncomeQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("account", "income_type").filter(
            income_type__journal=user.journal
        )

    def incomes(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(user)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("account__pk"))
            .order_by("year", "account")
        )
