from django.db import models
from django.db.models import F, Q, Sum
from django.db.models.functions import ExtractYear
from django.utils.translation import gettext as _

from ..core.mixins.queryset_sum import SumMixin
from ..users.models import User


class SavingTypeQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("journal").filter(journal=user.journal)

    def items(self, user: User, year=None):
        _year = year or user.year
        return self.related(user).filter(Q(closed__isnull=True) | Q(closed__gte=_year))


class SavingQuerySet(SumMixin, models.QuerySet):
    def related(self, user: User):
        return self.select_related("account", "saving_type").filter(
            saving_type__journal=user.journal
        )

    def incomes(self, user: User):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.related(user)
            .annotate(year=ExtractYear(F("date")))
            .values("year", "saving_type__title")
            .annotate(incomes=Sum("price"), fee=Sum("fee"))
            .values("year", "incomes", "fee", category_id=F("saving_type__pk"))
            .order_by("year", "category_id")
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


class SavingBalanceQuerySet(models.QuerySet):
    def related(self, user: User):
        return self.select_related("saving_type").filter(
            saving_type__journal=user.journal
        )

