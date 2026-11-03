from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from django.db.models import Max, QuerySet

from ...savings.models import SavingType
from ..close_rules import CloseRule, Removed


@dataclass(frozen=True)
class FundCloseYear:
    """A fund's close year under a move's close rule; its last move is a sell's or a
    switch out's."""

    fund: SavingType

    @classmethod
    def follow(cls, fund_pk: int, close: CloseRule) -> None:
        close_year = cls._load(fund_pk)

        closed = close.year(close_year.fund.closed, close_year.last_move)
        if close_year.fund.closed == closed:
            return

        # no type save: the move's receiver syncs savings once, after this
        SavingType.objects.filter(pk=fund_pk).update(closed=closed)

    @classmethod
    def follow_removed(cls, removed: Iterable[Removed]) -> None:
        for move in removed:
            cls.follow(move.fund_pk, move)

    @classmethod
    def is_closing_move(cls, fund_pk: int, day: date) -> bool:
        return cls._load(fund_pk).closes(day)

    @classmethod
    def of_funds(cls, fund_pks: Iterable[int]) -> dict[int, "FundCloseYear"]:
        return {fund.pk: cls(fund) for fund in cls._funds().filter(pk__in=fund_pks)}

    @classmethod
    def _load(cls, fund_pk: int) -> "FundCloseYear":
        return cls(cls._funds().get(pk=fund_pk))

    @staticmethod
    def _funds() -> QuerySet[SavingType]:
        return SavingType.objects.annotate(
            last_sell=Max("savings_close_from__date"),
            last_switch=Max("savings_change_from__date"),
        )

    def closes(self, day: date) -> bool:
        return day.year == self.fund.closed and day >= self.last_move

    @property
    def last_move(self) -> date:
        moves = (self.fund.last_sell, self.fund.last_switch)
        # no move left: date.min, so a removed move is later than the rest
        return max((day for day in moves if day), default=date.min)
