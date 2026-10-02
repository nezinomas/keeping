from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import NamedTuple

from django.db.models import F, Sum, Value
from django.db.models.functions import ExtractYear

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import DatedModelService
from .. import models


class CommonMethodsMixin:
    def year(self, year):
        return self.objects.filter(date__year=year)

    def items(self):
        return self.objects.all()

    def incomes(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "to_account__title")
            .annotate(incomes=Sum("price"))
            .values("year", "incomes", category_id=F("to_account__pk"))
            .order_by("year", "category_id")
        )

    def base_expenses(self, fee=False):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        values = ["year", "expenses"]

        if fee:
            values.append("fee")

        # Annotate the total price for each year and account
        objects = (
            self.objects.annotate(year=ExtractYear(F("date")))
            .values("year", "from_account__title")
            .annotate(expenses=Sum("price"))
        )

        # Annotate the total fee for each year and account if fee is True
        objects = objects.annotate(fee=Sum("fee")) if fee else objects

        return objects.values(*values, category_id=F("from_account__pk")).order_by(
            "year", "category_id"
        )


class TransactionModelService(CommonMethodsMixin, DatedModelService):
    def get_queryset(self):
        return models.Transaction.objects.select_related(
            "from_account", "to_account"
        ).filter(
            from_account__journal=self.user.journal,
            to_account__journal=self.user.journal,
        )

    def expenses(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses()


class SavingCloseModelService(SumMixin, CommonMethodsMixin, DatedModelService):
    def get_queryset(self):
        return models.SavingClose.objects.select_related(
            "from_account", "to_account"
        ).filter(
            from_account__journal=self.user.journal,
            to_account__journal=self.user.journal,
        )

    def sum_by_month(self, year, month=None):
        return self.month_sum(self.objects, year=year, month=month).annotate(
            title=Value("savings_close")
        )

    def expenses(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(fee=True)


class SavingChangeModelService(CommonMethodsMixin, DatedModelService):
    def get_queryset(self):
        return models.SavingChange.objects.select_related(
            "from_account", "to_account"
        ).filter(
            from_account__journal=self.user.journal,
            to_account__journal=self.user.journal,
        )

    def expenses(self):
        """
        Used only in the post_save signal.
        Calculates and returns the total price for each year
        """
        return self.base_expenses(fee=True)

    def switched_within(self, year: int, types: list[str]) -> int:
        """
        Money switched up to `year` into funds of `types` still on the table
        that started in one, however many closed funds it passed through, in cents.
        """
        rows = self.objects.filter(
            date__year__lte=year,
            from_account__type__in=types,
            to_account__type__in=types,
        ).values_list(
            "pk",
            "date",
            "from_account_id",
            "to_account_id",
            "from_account__closed",
            "to_account__closed",
            "price",
        )
        return SwitchedWithin.total([Switch(*row) for row in rows], year)


class Switch(NamedTuple):
    pk: int
    date: date
    source: int
    target: int
    source_closed: int | None
    target_closed: int | None
    price: int


@dataclass
class SwitchedWithin:
    """Walks switches in date order, tracking per fund the money that started on
    the table and sits in it."""

    year: int
    started: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    taken_off: int = 0

    @classmethod
    def total(cls, switches: list[Switch], year: int) -> int:
        walk = cls(year)
        for switch in sorted(switches, key=walk.order):
            walk.add(switch)
        return walk.taken_off

    def on_table(self, closed: int | None) -> bool:
        return closed is None or closed >= self.year

    def order(self, switch: Switch) -> tuple:
        # within a day, money reaches a closed fund before it can leave it
        return (
            switch.date,
            self.on_table(switch.target_closed),
            not self.on_table(switch.source_closed),
            switch.pk,
        )

    def add(self, switch: Switch) -> None:
        moved = switch.price
        if not self.on_table(switch.source_closed):
            # Each unit of closed money moves on once, so the pool is drawn down.
            moved = min(switch.price, self.started[switch.source])
            self.started[switch.source] -= moved
        self.started[switch.target] += moved
        if self.on_table(switch.target_closed):
            self.taken_off += moved
