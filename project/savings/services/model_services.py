from datetime import date

from django.db.models import (
    Case,
    F,
    IntegerField,
    Model,
    Q,
    QuerySet,
    Sum,
    Value,
    When,
)
from django.db.models.expressions import Combinable
from django.db.models.functions import Coalesce, ExtractYear, TruncMonth

from ...core.lib.date import last_months_window
from ...core.lib.table_columns import SAVINGS
from ...core.mixins.sum import SumMixin
from ...core.services.model_services import (
    BaseModelService,
    DatedModelService,
    max_year,
)
from .. import models

CHARGED = Q(saving_type__fee_source=models.SavingType.FeeSource.ACCOUNT)
YearRows = tuple[tuple[QuerySet, Combinable], ...]


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
        year = year or self.user.selected_year()
        return self.objects.filter(Q(closed__isnull=True) | Q(closed__gte=year))

    def latest_row_year(self, fund: models.SavingType) -> int:
        if not fund.pk:
            return 0

        return max_year(*_rows_but_moves(fund), *_moves(fund))

    def latest_year_but_moves_without(
        self, fund: models.SavingType, move: Model
    ) -> int:
        return max_year(*_without(_rows_but_moves(fund), move))

    def last_move_year_without(self, fund: models.SavingType, move: Model) -> int:
        return max_year(*_without(_moves(fund), move))


def _rows_but_moves(fund: models.SavingType) -> YearRows:
    year = ExtractYear("date")
    return (
        (fund.saving_set.all(), year),
        (fund.savings_change_to.all(), year),
        (fund.savings_worth.all(), year),
        (fund.savingplan_set.all(), F("year")),
    )


def _moves(fund: models.SavingType) -> YearRows:
    year = ExtractYear("date")
    return (
        (fund.savings_close_from.all(), year),
        (fund.savings_change_from.all(), year),
    )


def _without(rows: YearRows, move: Model) -> YearRows:
    # a sell and a switch may share a pk: `move` leaves only its own model's rows
    return tuple(
        (qs.exclude(pk=move.pk) if qs.model is type(move) else qs, year)
        for qs, year in rows
    )


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
        return self.month_sum(self.objects, year).annotate(title=Value(SAVINGS))

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

    def spent_last_months(self, today: date, months: int = 6):
        """The savings of the `months` whole months before `today`'s, with the
        account-charged fees, which leave on top of them."""
        return self._in_last_months(today, months).aggregate(
            sum=Coalesce(Sum(self._cash_out()), 0)
        )

    def _account_charged(self):
        return self.objects.filter(CHARGED, fee__gt=0)

    def _in_last_months(self, today: date, months: int):
        return self.objects.filter(date__range=last_months_window(today, months))

    def sum_by_month_and_type(self, year: int):
        return (
            self.objects.filter(date__year=year)
            .values("saving_type")
            .annotate(date=TruncMonth("date"))
            .values("date")
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
            title=Value(SAVINGS)
        )

    def incomes(self):
        return (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "saving_type__title")
            .annotate(incomes=Sum("price"), fee=Sum("fee"))
            .values("year", "incomes", "fee", category_id=F("saving_type__pk"))
            .order_by("year", "category_id")
        )

    def expenses(self):
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
            When(CHARGED, then=F("price") + F("fee")),
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
