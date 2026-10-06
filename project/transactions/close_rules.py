from dataclasses import dataclass
from datetime import date


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
