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
        return self.objects.filter(closed=False)

    def year(self, year):
        return self.objects.filter(
            Q(date__year=year) | (Q(date__year__lt=year) & Q(closed=False))
        )

    def sum_by_month(self, year, closed=False):
        qs = self.objects

        if not closed:
            qs = qs.filter(closed=False)

        return (
            qs.filter(date__year=year)
            .annotate(cnt=Count("id"))
            .values("id")
            .annotate(date=TruncMonth("date"))
            .values("date")
            .annotate(sum_debt=Sum("price"))
            .annotate(sum_return=Sum("returned"))
            .annotate(title=Value(f"{self.debt_type}"))
            .order_by("date")
        )

    def sum_all(self):
        return self.objects.filter(closed=False).aggregate(
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
        return (
            self.objects.filter(debt=debt_return_instance.debt).aggregate(
                total=Sum("price")
            )["total"]
            or 0
        )
