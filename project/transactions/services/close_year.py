from dataclasses import dataclass
from datetime import date

from django.db.models import Max

from ...savings.models import SavingType
from ..close_rules import KEEP, CloseRule


@dataclass(frozen=True)
class FundCloseYear:
    """A fund's close year under a move's close rule; its last move is a sell's or a
    switch out's."""

    fund: SavingType

    @classmethod
    def follow(cls, fund_pk: int, close: CloseRule = KEEP) -> None:
        close_year = cls._load(fund_pk)

        closed = close.year(close_year.fund.closed, close_year.last_move)
        if close_year.fund.closed == closed:
            return

        # no type save: the move's receiver syncs savings once, after this
        SavingType.objects.filter(pk=fund_pk).update(closed=closed)

    @classmethod
    def is_closing_move(cls, fund_pk: int, day: date) -> bool:
        close_year = cls._load(fund_pk)

        return day.year == close_year.fund.closed and day >= close_year.last_move

    @classmethod
    def _load(cls, fund_pk: int) -> "FundCloseYear":
        return cls(
            SavingType.objects.annotate(
                last_sell=Max("savings_close_from__date"),
                last_switch=Max("savings_change_from__date"),
            ).get(pk=fund_pk)
        )

    @property
    def last_move(self) -> date:
        moves = (self.fund.last_sell, self.fund.last_switch)
        # no move left: date.min, so a removed move is later than the rest
        return max((day for day in moves if day), default=date.min)
