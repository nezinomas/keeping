from dataclasses import dataclass

from django.db.models import Max

from ...savings.models import SavingType
from ..close_rules import KEEP, CloseBox, KeepClose


@dataclass(frozen=True)
class FundCloseYear:
    """A fund closes in the year of its last move: a sell or a switch out."""

    fund: SavingType

    @classmethod
    def follow(cls, fund_pk: int, close: KeepClose | CloseBox = KEEP) -> None:
        fund = SavingType.objects.annotate(
            last_sell=Max("savings_close_from__date"),
            last_switch=Max("savings_change_from__date"),
        ).get(pk=fund_pk)

        closed = cls(fund)._year(close)
        if fund.closed == closed:
            return

        # no type save: the move's receiver syncs savings once, after this
        SavingType.objects.filter(pk=fund_pk).update(closed=closed)

    def _year(self, close: KeepClose | CloseBox) -> int | None:
        moves = [day for day in (self.fund.last_sell, self.fund.last_switch) if day]
        if not moves:
            return None

        return close.year(self.fund.closed, max(moves))
