from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import ExtractYear

from ..core.lib import utils
from ..core.mixins.queryset_sum import SumMixin


class PensionTypeQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return self.select_related("journal").filter(journal=journal)

    def items(self, year: int = None):
        return self.related()


class PensionQuerySet(SumMixin, models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return self.select_related("pension_type").filter(pension_type__journal=journal)

    def year(self, year):
        return self.related().filter(date__year=year)

    def items(self):
        return self.related().all()

    def incomes(self):
        return (
            self.related()
            .annotate(year=ExtractYear(F("date")))
            .values("year", "pension_type__title")
            .annotate(incomes=Sum("price"), fee=Sum("fee"))
            .values("year", "incomes", "fee", id=F("pension_type__pk"))
            .order_by("year", "id")
        )


class PensionBalanceQuerySet(models.QuerySet):
    def related(self):
        journal = utils.get_user().journal
        return self.select_related("pension_type").filter(pension_type__journal=journal)

    def items(self):
        return self.related()

    def year(self, year: int):
        return self.related().filter(year=year)

    def sum_by_year(self):
        return (
            self.related()
            .annotate(y=F("year"))
            .values("y")
            .annotate(incomes=Sum("incomes"), profit=Sum("profit_sum"))
            .order_by("year")
            .values("year", "incomes", "profit")
        )
