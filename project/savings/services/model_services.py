from datetime import date, timedelta
from typing import Optional

from dateutil.relativedelta import relativedelta
from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import Coalesce, ExtractYear, TruncMonth
from django.utils.translation import gettext as _

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService
from .. import models


class SavingTypeModelService(BaseModelService):
    def get_queryset(self):
        return models.SavingType.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def year(self, year):
        raise NotImplementedError(
            "SavingTypeModelService.year is not implemented. Use items() instead."
        )

    def all(self):
        return self.objects.all()

    def none(self):
        return self.objects.none()

    def items(self, year=None):
        year = year or self.user.year
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))


class SavingModelService(SumMixin, BaseModelService):
    def get_queryset(self):
        return models.Saving.objects.select_related("account", "saving_type").filter(
            saving_type__journal=self.user.journal
        )

    def year(self, year):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects

    def sum_by_year(self):
        return self.year_sum(self.objects)

    def sum_by_month(self, year: int, month: Optional[int] = None):
        return self.month_sum(self.objects, year, month).annotate(
            title=Value("savings")
        )

    def sum_by_month_and_type(self, year: int):
        return (
            self.objects.filter(date__year=year)
            .annotate(cnt=Count("saving_type"))
            .values("saving_type")
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(c=Count("id"))
            .annotate(sum=Sum("price"))
            .order_by("saving_type__title", "date")
            .values("date", "sum", title=F("saving_type__title"))
        )

    def sum_by_day_and_type(self, year: int, month: int):
        return self.day_sum(self.objects, year=year, month=month).values(
            "date", "sum", title=F("saving_type__title")
        )

    def sum_by_day(self, year: int, month: int):
        return self.day_sum(self.objects, year=year, month=month).annotate(
            title=Value("savings")
        )

    def last_months(self, months: int = 6):
        """
        Calculates the total sum of savings for the last `months` months.
        If today is 2020-02-15 and months=6, it will calculate
        the sum from 2019-08-01 to 2020-01-31.
        - If there are no savings in that period, it will return 0.
        """
        start = date.today().replace(day=1) - timedelta(days=1)

        # back months to past; if months=6 then end=2019-08-01
        end = (start + timedelta(days=1)) - relativedelta(months=months)

        return self.objects.filter(date__range=(end, start)).aggregate(
            sum=Coalesce(Sum("price"), 0)
        )

    def incomes(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "saving_type__title")
            .annotate(incomes=Sum("price"), fee=Sum("fee"))
            .values("year", "incomes", "fee", category_id=F("saving_type__pk"))
            .order_by("year", "category_id")
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
            .order_by("year", "category_id")
        )


class SavingBalanceModelService(BaseModelService):
    def get_queryset(self):
        return models.SavingBalance.objects.select_related("saving_type").filter(
            saving_type__journal=self.user.journal
        )

    def items(self):
        return self.objects

    def year(self, year: int, types=None):
        qs = self.objects.filter(year=year)

        if types:
            qs = qs.filter(saving_type__type__in=types)

        return qs.order_by("saving_type__type", "saving_type__title")

    def sum_by_type(self):
        return (
            self.objects.annotate(cnt=Count("saving_type"))
            .values("saving_type__type")
            .annotate(y=F("year"))
            .values("y")
            .filter(
                Q(saving_type__closed__isnull=True) | Q(saving_type__closed__gt=F("y"))
            )
            .annotate(incomes=Sum("incomes"), profit=Sum("profit_sum"), fee=Sum("fee"))
            .order_by("year")
            .values("year", "incomes", "profit", "fee", type=F("saving_type__type"))
        )

    def sum_by_year(self):
        return (
            self.objects.annotate(y=F("year"))
            .values("y")
            .annotate(incomes=Sum("incomes"), profit=Sum("profit_sum"))
            .order_by("year")
            .values("year", "incomes", "profit")
        )
