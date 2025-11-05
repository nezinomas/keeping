from datetime import date, timedelta
from typing import Optional, cast

from dateutil.relativedelta import relativedelta
from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import TruncMonth
from django.utils.translation import gettext as _

from ...users.models import User
from ..managers import SavingBalanceQuerySet, SavingQuerySet, SavingTypeQuerySet
from ..models import Saving, SavingBalance, SavingType


class SavingTypeModelService:
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(SavingTypeQuerySet, SavingType.objects)

    def none(self):
        return SavingType.objects.none()

    def items(self, year=None):
        _year = year or self.user.year
        return self.model.related(self.user).filter(
            Q(closed__isnull=True) | Q(closed__gte=_year)
        )

    def all(self):
        return self.model.related(self.user)


class SavingModelService:
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(SavingQuerySet, Saving.objects)

    def year(self, year):
        return self.model.related(self.user).filter(date__year=year)

    def items(self):
        return self.model.related(self.user)

    def sum_by_year(self):
        return self.model.related(self.user).year_sum()

    def sum_by_month(self, year: int, month: Optional[int] = None):
        return (
            self.model.related(self.user)
            .month_sum(year, month)
            .annotate(title=Value("savings"))
        )

    def sum_by_month_and_type(self, year: int):
        return (
            self.model.related(self.user)
            .filter(date__year=year)
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
        return (
            self.model.related(self.user)
            .day_sum(year=year, month=month)
            .values("date", "sum", title=F("saving_type__title"))
        )

    def sum_by_day(self, year: int, month: int):
        return (
            self.model.related(self.user)
            .day_sum(year=year, month=month)
            .annotate(title=Value(_("Savings")))
        )

    def last_months(self, months: int = 6) -> float:
        # previous month
        # if today February, then start is 2020-01-31
        start = date.today().replace(day=1) - timedelta(days=1)

        # back months to past; if months=6 then end=2019-08-01
        end = (start + timedelta(days=1)) - relativedelta(months=months)

        return (
            self.model.related(self.user)
            .filter(date__range=(end, start))
            .aggregate(sum=Sum("price"))
        )


class SavingBalanceModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.user = user
        self.model = cast(SavingBalanceQuerySet, SavingBalance.objects)

    def items(self):
        return self.model.related(self.user)

    def year(self, year: int, types=None):
        qs = self.model.related(self.user).filter(year=year)

        if types:
            qs = qs.filter(saving_type__type__in=types)

        return qs.order_by("saving_type__type", "saving_type__title")

    def sum_by_type(self):
        return (
            self.model.related(self.user)
            .annotate(cnt=Count("saving_type"))
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
            self.model.related(self.user)
            .annotate(y=F("year"))
            .values("y")
            .annotate(incomes=Sum("incomes"), profit=Sum("profit_sum"))
            .order_by("year")
            .values("year", "incomes", "profit")
        )
