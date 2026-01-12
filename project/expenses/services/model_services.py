from datetime import date, timedelta
from typing import cast

from dateutil.relativedelta import relativedelta
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    F,
    Func,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import (
    Cast,
    Concat,
    ExtractYear,
    TruncDay,
    TruncMonth,
    TruncYear,
)
from django.urls import reverse

from .. import managers, models
from ...core.services.model_services import BaseModelService


class ExpenseTypeModelService(BaseModelService[managers.ExpenseTypeQuerySet]):
    def get_queryset(self):
        return cast(managers.ExpenseTypeQuerySet, models.ExpenseType.objects).related(
            self.user
        )

    def year(self, year: int):
        raise NotImplementedError(
            "ExpenseTypeModelService.year is not implemented. Use items() instead."
        )

    def items(self):
        return self.objects


class ExpenseNameModelService(BaseModelService[managers.ExpenseNameQuerySet]):
    def get_queryset(self):
        return cast(managers.ExpenseNameQuerySet, models.ExpenseName.objects).related(
            self.user
        )

    def year(self, year: int):
        return self.objects.filter(Q(valid_for__isnull=True) | Q(valid_for=year))

    def items(self):
        return self.objects

    def none(self):
        return self.objects.none()


class ExpenseModelService(BaseModelService[managers.ExpenseQuerySet]):
    def get_queryset(self):
        return cast(managers.ExpenseQuerySet, models.Expense.objects).related(self.user)

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

    def expenses_list(self, qs):
        """
        Accepts ANY filtered queryset (by year, month, or search)
        and applies the high-performance formatting, annotations, and .values().
        """

        # 1. Calculate URL patterns (Dynamic Annotation Strategy)
        dummy_id = 0
        update_pattern = reverse("expenses:update", args=[dummy_id])
        delete_pattern = reverse("expenses:delete", args=[dummy_id])

        # Split patterns to get prefix/suffix
        u_prefix, u_suffix = update_pattern.split(str(dummy_id))
        d_prefix, d_suffix = delete_pattern.split(str(dummy_id))

        # 2. Apply all Annotations & Optimizations to the incoming QS
        return (
            qs.annotate(
                # Database-level Price Formatting (MariaDB/MySQL)
                price_str=Func(
                    F("price") / Value(100.0),
                    Value(2),
                    Value("lt_LT"),
                    function="FORMAT",
                    output_field=CharField(),
                ),
                # PDF detection
                is_pdf=Case(
                    When(attachment__endswith=".pdf", then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
                # Grouping for "If Month Changed" logic
                month_group=TruncMonth("date"),
                # Fast URL Construction
                url_update=Concat(
                    Value(u_prefix),
                    Cast("id", output_field=CharField()),
                    Value(u_suffix),
                    output_field=CharField(),
                ),
                url_delete=Concat(
                    Value(d_prefix),
                    Cast("id", output_field=CharField()),
                    Value(d_suffix),
                    output_field=CharField(),
                ),
            )
            .order_by("-date", "expense_type__title", F("expense_name__title").asc())
            .values(
                "id",
                "date",
                "account__title",
                "expense_type__pk",
                "expense_type__title",
                "expense_name__title",
                "quantity",
                "remark",
                "attachment",
                "exception",
                "price_str",
                "is_pdf",
                "month_group",
                "url_update",
                "url_delete",
            )
        )
