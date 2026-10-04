from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import NamedTuple

from django.db.models import F, Sum, Value
from django.db.models.functions import Coalesce, ExtractYear

from ...core.mixins.sum import SumMixin
from ...core.services.model_services import DatedModelService
from ...savings.models import Saving
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

    def moves(self):
        """
        Used only in the post_save signal.
        One row per move out of a fund, with the money `expenses` counts as sold
        """
        return self.objects.values("date", "price", category_id=F("from_account__pk"))

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


class Purchase(NamedTuple):
    date: date
    fund: int
    price: int


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

    def switched_within(
        self, year: int, types: list[str], hidden: frozenset[int] = frozenset()
    ) -> int:
        """
        Money switched up to `year` into funds of `types` still on the table
        that started in one, however many closed funds it passed through, in cents.
        A fund in `hidden` (its row shows no profit) is off the table like a closed one.
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
        return SwitchedWithin.total(
            [Switch(*row) for row in rows],
            year,
            hidden,
            purchases_of=lambda funds: self._purchases(funds, year),
        )

    @staticmethod
    def _purchases(funds: set[int], year: int) -> list[Purchase]:
        if not funds:
            return []
        rows = (
            Saving.objects.filter(saving_type_id__in=funds, date__year__lte=year)
            .values("date", "saving_type_id")
            .annotate(total=Coalesce(Sum("price"), 0))
            .order_by()
            .values_list("date", "saving_type_id", "total")
        )
        return [Purchase(*row) for row in rows]


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
    """Walks purchases and switches in date order, tracking per fund the money that
    came in from the table and all the money that came in."""

    year: int
    hidden: frozenset[int] = frozenset()
    from_table: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    paid_in: defaultdict[int, int] = field(default_factory=lambda: defaultdict(int))
    taken_off: int = 0

    @classmethod
    def total(
        cls,
        switches: list[Switch],
        year: int,
        hidden: frozenset[int],
        purchases_of: Callable[[set[int]], list[Purchase]],
    ) -> int:
        walk = cls(year, hidden)
        sources = {s.source for s in switches if walk.source_off_table(s)}
        # a purchase's (date,) sorts before every switch of its day
        events = [((p.date,), walk.buy, p) for p in purchases_of(sources)]
        events += [(walk.order(s), walk.add, s) for s in switches]
        for _, handle, event in sorted(events, key=lambda x: x[0]):
            handle(event)
        return walk.taken_off

    def source_off_table(self, switch: Switch) -> bool:
        return not self.on_table(switch.source, switch.source_closed)

    def on_table(self, fund: int, closed: int | None) -> bool:
        return fund not in self.hidden and (closed is None or closed >= self.year)

    def order(self, switch: Switch) -> tuple:
        # within a day, money reaches a closed fund before it can leave it
        return (
            switch.date,
            self.on_table(switch.target, switch.target_closed),
            self.source_off_table(switch),
            switch.pk,
        )

    def buy(self, purchase: Purchase) -> None:
        self.paid_in[purchase.fund] += purchase.price

    def add(self, switch: Switch) -> None:
        moved = switch.price
        if self.source_off_table(switch):
            moved = self.table_share(switch.source, switch.price)
        self.from_table[switch.target] += moved
        self.paid_in[switch.target] += switch.price
        if self.on_table(switch.target, switch.target_closed):
            self.taken_off += moved

    def table_share(self, fund: int, price: int) -> int:
        # what leaves an off-table fund, gain included, splits as its money came in
        if not self.paid_in[fund]:
            return 0
        share, rest = divmod(price * self.from_table[fund], self.paid_in[fund])
        return share + (2 * rest >= self.paid_in[fund])
