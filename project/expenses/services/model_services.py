from datetime import date, timedelta
from typing import cast

from dateutil.relativedelta import relativedelta
from django.db.models import Case, Count, F, Q, Sum, Value, When
from django.db.models.functions import (
    Concat,
    ExtractYear,
    TruncDay,
    TruncMonth,
    TruncYear,
)

from ...users.models import User
from .. import managers, models


class ExpenseTypeModelService:
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.ExpenseTypeQuerySet, models.ExpenseType.objects
        ).related(user)

    def items(self):
        return self.objects.all()


class ExpenseNameModelService:
    def __init__(
        self,
        user: User,
    ):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(
            managers.ExpenseNameQuerySet, models.ExpenseName.objects
        ).related(user)

    def year(self, year: int):
        return self.objects.filter(Q(valid_for__isnull=True) | Q(valid_for=year))

    def items(self):
        return self.objects

    def none(self):
        return models.ExpenseName.objects.none()


class ExpenseModelService:
    def __init__(self, user: User):
        if not user:
            raise ValueError("User required")

        if not user.is_authenticated:
            raise ValueError("Authenticated user required")

        self.objects = cast(managers.ExpenseQuerySet, models.Expense.objects).related(
            user
        )

    def year(self, year: int):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects.all()

    def sum_by_month(self, year: int):
        return self.objects.month_sum(year).annotate(title=Value("expenses"))

    def sum_by_month_and_type(self, year: int):
        """
        Sums expense_types by month

        return:
        list of dictionaries: {'date': date.datete, 'sum': int, 'title': str}
        """

        return (
            self.objects.filter(date__year=year)
            .annotate(cnt=Count("expense_type"))
            .values("expense_type")
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(c=Count("id"), sum=Sum("price"))
            .order_by("date")
            .values("date", "sum", title=F("expense_type__title"))
        )

    def sum_by_month_and_name(self, year: int):
        return (
            self.objects.filter(date__year=year)
            .annotate(cnt=Count("expense_type"))
            .values("expense_type")
            .annotate(cnt=Count("expense_name"))
            .values("expense_name")
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(c=Count("id"), sum=Sum("price"))
            .order_by("expense_name__title", "date")
            .values(
                "date",
                "sum",
                title=F("expense_name__title"),
                type_title=F("expense_type__title"),
            )
        )

    def sum_by_day_ant_type(self, year: int, month: int):
        # Todo: refactore mistyped method name
        return (
            self.objects.filter(date__year=year, date__month=month)
            .annotate(cnt_id=Count("id"))
            .values("cnt_id")
            .annotate(date=TruncDay("date"))
            .values("date")
            .annotate(
                sum=Sum("price"),
                exception_sum=Sum(Case(When(exception=1, then="price"), default=0)),
            )
            .order_by("date")
            .values("date", "sum", "exception_sum", title=F("expense_type__title"))
        )

    def sum_by_year(self):
        return self.objects.year_sum()

    def sum_by_year_type(self, expense_type: list | None = None):
        return (
            self.objects.filter_types(expense_type)
            .annotate(cnt=Count("expense_type"))
            .values("expense_type")
            .annotate(
                date=TruncYear("date"), year=ExtractYear(F("date")), sum=Sum("price")
            )
            .order_by("year")
            .values("year", "sum", title=F("expense_type__title"))
        )

    def sum_by_year_name(self, expense_name: list | None = None):
        return (
            self.objects.filter_names(expense_name)
            .annotate(cnt=Count("expense_name"))
            .values("expense_name")
            .annotate(
                date=TruncYear("date"), year=ExtractYear(F("date")), sum=Sum("price")
            )
            .order_by("year")
            .values(
                "year",
                "sum",
                title=Concat(
                    "expense_name__parent__title", Value(" / "), "expense_name__title"
                ),
            )
        )

    def last_months(self, months: int = 6):
        # previous month
        # if today February, then start is 2020-01-31
        one_day = timedelta(days=1)
        start = date.today().replace(day=1) - one_day

        # back months to past; if months=6 then end=2019-08-01
        end = (start + one_day) - relativedelta(months=months)

        return (
            self.objects.filter(date__range=(end, start))
            .values("expense_type")
            .annotate(sum=Sum("price"))
            .values("sum", title=F("expense_type__title"))
        )
