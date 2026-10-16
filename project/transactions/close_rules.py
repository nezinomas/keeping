from dataclasses import dataclass
from datetime import date


class KeepClose:
    """No word from the user: the close year stays as it is."""

    def year(self, closed: int | None, last: date) -> int | None:
        return closed


KEEP = KeepClose()


@dataclass(frozen=True)
class CloseBox:
    """The *Uždaryti* box as submitted with a move: whether the user changed it, and
    its state."""

    changed: bool
    ticked: bool

    def year(self, closed: int | None, last: date) -> int | None:
        if not self.changed:
            return closed

        if self.ticked:
            return last.year

        return None


@dataclass(frozen=True)
class Removed:
    """A move deleted from its fund, or moved to another, dated `day` as loaded."""

    day: date

    def year(self, closed: int | None, last: date) -> int | None:
        # strictly later: a move left on the same day is the closing move now
        if self.day.year == closed and self.day > last:
            return None

        return closed


CloseRule = KeepClose | CloseBox | Removed
