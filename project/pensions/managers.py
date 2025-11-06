from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import ExtractYear

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class PensionTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("journal").filter(journal=user.journal)


class PensionQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("pension_type").filter(
            pension_type__journal=user.journal
        )

    def incomes(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(user)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "pension_type__title")
            .annotate(incomes=Sum("price"), fee=Sum("fee"))
            .values("year", "incomes", "fee", category_id=F("pension_type__pk"))
            .order_by("year", "id")
        )


class PensionBalanceQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("pension_type").filter(
            pension_type__journal=user.journal
        )
