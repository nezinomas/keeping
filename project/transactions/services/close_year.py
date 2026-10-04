from dataclasses import dataclass
from datetime import date

from django.db.models import Max

from ...savings.models import SavingType


class KeepClose:
    """No word from the user: a closed fund stays closed, at its last move."""

    def year(self, closed: int | None, last: date) -> int | None:
        return last.year if closed else None


KEEP = KeepClose()


@dataclass(frozen=True)
class CloseBox:
    """The *Uždaryti* box as submitted with a move, and the move's dates in its fund:
    after the save, and before it on an edit."""

    ticked: bool
    dates: tuple[date, ...]

    def year(self, closed: int | None, last: date) -> int | None:
        if self.ticked:
            return last.year

        # unticked on the move that is, or was, the fund's last one
        if max(self.dates) >= last:
            return None

        return KEEP.year(closed, last)


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
            return  # a type save re-syncs savings; skip it when nothing changed

        fund.closed = closed
        fund.save()

    def _year(self, close: KeepClose | CloseBox) -> int | None:
        moves = [day for day in (self.fund.last_sell, self.fund.last_switch) if day]
        if not moves:
            return None

        return close.year(self.fund.closed, max(moves))
