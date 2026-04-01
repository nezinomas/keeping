from typing import cast

from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import TruncMonth

from ...core.services.model_services import BaseModelService
from ...users.models import User
from .. import managers, models


class DebtModelService(BaseModelService):
    def __init__(self, user: User, debt_type: str):
        self.debt_type = debt_type

        super().__init__(user)

    def get_queryset(self):
        return cast(managers.DebtQuerySet, models.Debt.objects).related(
            self.user, self.debt_type
        )

    def items(self):
        return self.objects.all()

    def open_items(self):
        return self.objects.filter(closed=False)

    def year(self, year):
        return self.objects.filter(
            Q(date__year=year) | (Q(date__year__lt=year) & Q(closed=False))
        )

    def sum_by_month(self, year, closed=False):
        qs = self.objects if closed else self.open_items()

        aggregated = (
            qs.filter(date__year=year)
            .annotate(month=TruncMonth("date"))
            .values("month")  # Safe grouping, no ORM conflict
            .annotate(
                sum_debt=Sum("price"),
                sum_return=Sum("returned"),
                title=Value(self.debt_type)
            )
            .order_by("month")
        )

        # Rename 'month' back to 'date' at the Python level
        return [
            {"date": row.pop("month"), **row} for row in aggregated
        ]

    def sum_all(self):
        return self.open_items().aggregate(
            debt=Sum("price"), debt_return=Sum("returned")
        )


class DebtReturnModelService(BaseModelService[managers.DebtReturnQuerySet]):
    def __init__(self, user: User, debt_type: str):
        self.debt_type = debt_type

        super().__init__(user)

    def get_queryset(self):
        return cast(managers.DebtReturnQuerySet, models.DebtReturn.objects).related(
            self.user, self.debt_type
        )

    def items(self):
        return self.objects.all()

    def year(self, year):
        return self.objects.filter(date__year=year)

    def sum_by_month(self, year):
        qs = self.objects

        return (
            qs.filter(date__year=year)
            .annotate(cnt=Count("id"))
            .values("id")
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(sum=Sum("price"))
            .annotate(title=Value(f"{self.debt_type}_return"))
            .order_by("date")
        )

    def total_returned_for_debt(self, debt_return_instance):
        result = self.objects.filter(debt=debt_return_instance.debt).aggregate(
            total=Sum("price")
        )
        return result.get("total") or 0
