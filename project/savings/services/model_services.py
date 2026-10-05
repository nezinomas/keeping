from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Case, Count, F, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce, ExtractYear, TruncMonth

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import BaseModelService, DatedModelService
from .. import models


class SavingTypeModelService(BaseModelService):
    def get_queryset(self):
        return models.SavingType.objects.select_related("journal").filter(
            journal=self.user.journal
        )

    def all(self):
        return self.objects.all()

    def none(self):
        return self.objects.none()

    def items(self, year=None):
        year = year or self.user.year
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))


class SavingModelService(SumMixin, DatedModelService):
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

    def sum_by_month(self, year: int):
        return self.month_sum(self.objects, year).annotate(title=Value("savings"))

    def cash_flow_by_month(self, year: int):
        """The savings series and the account fees on top of it, in one query."""
        return (
            self.sum_by_month(year)
            .order_by()
            .union(self.account_fees_by_month(year).order_by(), all=True)
            .order_by("date")
        )

    def account_fees_by_month(self, year: int):
        """Fees the accounts paid on top of the invested price, for the cash flow."""
        return self.month_sum(self._account_charged(), year, sum_column="fee").annotate(
            title=Value("savings_account_fee")
        )

    def account_fees_by_day(self, year: int, month: int):
        return self.day_sum(
            self._account_charged(), year, month, sum_column="fee"
        ).annotate(title=Value("savings_account_fee"))

    def spent_last_months(self, months: int = 6):
        """`last_months` with the account-charged fees, which leave on top of it."""
        charged = Q(saving_type__fee_source=models.SavingType.FeeSource.ACCOUNT)
        return self._in_last_months(self.objects, months).aggregate(
            sum=Coalesce(Sum("price"), 0) + Coalesce(Sum("fee", filter=charged), 0)
        )

    def _account_charged(self):
        return self.objects.filter(
            saving_type__fee_source=models.SavingType.FeeSource.ACCOUNT,
            fee__gt=0,
        )

    def _in_last_months(self, qs, months: int):
        start = date.today().replace(day=1) - timedelta(days=1)

        # back months to past; if months=6 then end=2019-08-01
        end = (start + timedelta(days=1)) - relativedelta(months=months)

        return qs.filter(date__range=(end, start))

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
        return self._in_last_months(self.objects, months).aggregate(
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
            .annotate(expenses=Sum(self._cash_out()))
            .values("year", "expenses", category_id=F("account__pk"))
            .order_by("year", "category_id")
        )

    @staticmethod
    def _cash_out():
        """What a purchase takes from its account."""
        return Case(
            When(
                saving_type__fee_source=models.SavingType.FeeSource.ACCOUNT,
                then=F("price") + F("fee"),
            ),
            default=F("price"),
            output_field=IntegerField(),
        )


class SavingBalanceModelService(DatedModelService):
    def get_queryset(self):
        return models.SavingBalance.objects.select_related("saving_type").filter(
            saving_type__journal=self.user.journal
        )

    def items(self):
        return self.objects

    def year(self, year: int):
        return self._year_ordered(self.objects.filter(year=year))

    def year_of_types(self, year: int, types):
        return self._year_ordered(
            self.objects.filter(year=year, saving_type__type__in=types)
        )

    @staticmethod
    def _year_ordered(qs):
        return qs.order_by("saving_type__type", "saving_type__title")

    def sum_by_type(self):
        """Per year and type, summed over the rows that show a profit."""
        return (
            self.objects.filter(models.SavingBalance.shows_profit_q())
            .values("year", type=F("saving_type__type"))
            .annotate(
                incomes=Sum("incomes"),
                profit=Sum("profit_sum"),
                total=Sum("market_value"),
                fee=Sum("fee"),
            )
            .order_by("year")
            .values("year", "incomes", "profit", "total", "fee", "type")
        )

    def sum_by_year(self):
        return (
            self.objects.annotate(y=F("year"))
            .values("y")
            .annotate(incomes=Sum("incomes"), profit=Sum("profit_sum"))
            .order_by("year")
            .values("year", "incomes", "profit")
        )
