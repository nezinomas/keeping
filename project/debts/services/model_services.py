from django.db.models import F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce, ExtractYear, TruncMonth

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import DatedModelService
from ...users.models import User
from .. import models


def _yearly_sums(objects, key):
    return (
        objects.annotate(year=ExtractYear("date"))
        .values("year", "account__title")
        .annotate(total=Sum("price"))
        .values("year", category_id=F("account__pk"), **{key: F("total")})
        .order_by("year", "category_id")
    )


class DebtModelService(DatedModelService):
    def __init__(self, user: User, debt_type: models.Debt.DebtType):
        self.debt_type = debt_type

        super().__init__(user)

    def get_queryset(self):
        return models.Debt.objects.select_related("account", "journal").filter(
            journal=self.user.journal, debt_type=self.debt_type
        )

    def items(self):
        return self.objects.all()

    def open_items(self):
        return self.objects.filter(closed=False)

    @classmethod
    def sync_returned(cls, journal_id: int, debt_type: models.Debt.DebtType):
        returns = (
            models.DebtReturn.objects.filter(debt=OuterRef("pk"))
            .order_by()
            .values("debt")
            .annotate(total=Sum("price"))
            .values("total")
        )
        # update(), not save(): no account source reads `returned`, so no second sync
        models.Debt.objects.filter(journal_id=journal_id, debt_type=debt_type).update(
            returned=Coalesce(Subquery(returns), 0)
        )

    def year(self, year):
        return self.objects.filter(
            Q(date__year=year) | (Q(date__year__lt=year) & Q(closed=False))
        )

    def sum_by_month(self, year, closed=False):
        qs = self.objects if closed else self.open_items()

        return (
            qs.filter(date__year=year)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                sum_debt=Sum("price"),
                sum_return=Sum("returned"),
                title=Value(self.debt_type),
                date=F("month"),
            )
            .order_by("month")
            .values("date", "title", "sum_debt", "sum_return")
        )

    def sum_all(self):
        return self.open_items().aggregate(
            debt=Coalesce(Sum("price"), 0), debt_return=Coalesce(Sum("returned"), 0)
        )

    def incomes(self):
        return _yearly_sums(self.objects, "incomes")

    def expenses(self):
        return _yearly_sums(self.objects, "expenses")


class DebtReturnModelService(SumMixin, DatedModelService):
    def __init__(self, user: User, debt_type: models.Debt.DebtType):
        self.debt_type = debt_type

        super().__init__(user)

    def get_queryset(self):
        return models.DebtReturn.objects.select_related("account", "debt").filter(
            debt__journal=self.user.journal, debt__debt_type=self.debt_type
        )

    def items(self):
        return self.objects.all()

    def year(self, year):
        return self.objects.filter(date__year=year)

    def sum_by_month(self, year):
        return (
            self.objects.filter(date__year=year)
            .annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                sum=Sum("price"),
                title=Value(f"{self.debt_type}_return"),
                date=F("month"),
            )
            .order_by("month")
            .values("date", "sum", "title")
        )

    def total_returned_for_debt(self, debt, leaving_out_pk=0):
        return (
            self.objects.filter(debt=debt)
            .exclude(pk=leaving_out_pk)
            .aggregate(total=Coalesce(Sum("price"), 0))["total"]
        )

    def incomes(self):
        return _yearly_sums(self.objects, "incomes")

    def expenses(self):
        return _yearly_sums(self.objects, "expenses")
