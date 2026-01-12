from datetime import date, timedelta
from typing import Optional, cast

from dateutil.relativedelta import relativedelta
from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import TruncMonth
from django.utils.translation import gettext as _

from .. import managers, models
from ...core.services.model_services import BaseModelService


class SavingTypeModelService(BaseModelService[managers.SavingTypeQuerySet]):
    def get_queryset(self):
        return cast(managers.SavingTypeQuerySet, models.SavingType.objects).related(
            self.user
        )

    def year(self, year):
        return self.objects

    def all(self):
        return self.objects

    def none(self):
        return self.objects.none()

    def items(self, year=None):
        year = year or self.user.year
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))


class SavingModelService(BaseModelService[managers.SavingQuerySet]):
    def get_queryset(self):
        return cast(managers.SavingQuerySet, models.Saving.objects).related(self.user)

    def year(self, year):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects

    def sum_by_year(self):
        return self.objects.year_sum()

    def sum_by_month(self, year: int, month: Optional[int] = None):
        return self.objects.month_sum(year, month).annotate(title=Value("savings"))

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
        return self.objects.day_sum(year=year, month=month).values(
            "date", "sum", title=F("saving_type__title")
        )

    def sum_by_day(self, year: int, month: int):
        return self.objects.day_sum(year=year, month=month).annotate(
            title=Value(_("Savings"))
        )

    def last_months(self, months: int = 6):
        # previous month
        # if today February, then start is 2020-01-31
        start = date.today().replace(day=1) - timedelta(days=1)

        # back months to past; if months=6 then end=2019-08-01
        end = (start + timedelta(days=1)) - relativedelta(months=months)

        return self.objects.filter(date__range=(end, start)).aggregate(sum=Sum("price"))


class SavingBalanceModelService(BaseModelService[managers.SavingBalanceQuerySet]):
    def get_queryset(self):
        return cast(
            managers.SavingBalanceQuerySet, models.SavingBalance.objects
        ).related(self.user)

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
