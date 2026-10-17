from dataclasses import dataclass
from datetime import date


class KeepClose:
    """No word from the user: the close year stays as it is."""

    def year(self, closed: int | None, last: date) -> int | None:
        return closed


KEEP = KeepClose()


class CloseFund:
    """The box ticked: the fund closes in its last move's year."""

    def year(self, closed: int | None, last: date) -> int:
        return last.year


CLOSE = CloseFund()


class ReopenFund:
    """The box unticked on the closing move: the fund is open again."""

    def year(self, closed: int | None, last: date) -> int | None:
        return None


REOPEN = ReopenFund()


@dataclass(frozen=True)
class Removed:
    """A move deleted from its fund, or moved to another, as loaded."""

    fund_pk: int
    day: date

    def year(self, closed: int | None, last: date) -> int | None:
        # strictly later: a move left on the same day is the closing move now
        if self.day.year == closed and self.day > last:
            return None

        return closed


CloseRule = KeepClose | CloseFund | ReopenFund | Removed
