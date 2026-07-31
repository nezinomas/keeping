from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol, TypeVar


class DatedRow(Protocol):
    """A row carrying the calendar date its amount was recorded on.

    Structural on purpose: the module that owns the row type
    (``drinks_stats.DataRow``) depends on this one, so this one must not
    depend back on it.
    """

    @property
    def date(self) -> date: ...


RowT = TypeVar("RowT", bound=DatedRow)


@dataclass(frozen=True)
class YearBoundary:
    """How far into one calendar year a metric may read.

    Two rules, both of which every lib reporting a year needs: the year under
    view runs to today while it is still running and to Dec 31 once it is over,
    and the year before it is only compared as far as the same month and day.
    """

    year: int
    today: date

    @classmethod
    def from_records(
        cls, records: Sequence[DatedRow] = (), today: date | None = None
    ) -> "YearBoundary":
        """The year the records belong to, falling back to today's year."""
        today = today or date.today()
        year = records[0].date.year if records else today.year
        return cls(year=year, today=today)

    @property
    def end_date(self) -> date:
        """Today while the year is running, Dec 31 once it is over."""
        if self.year == self.today.year:
            return self.today
        return date(self.year, 12, 31)

    @property
    def days_elapsed(self) -> int:
        """Days of the year covered — day-of-year today, 365 or 366 for a year
        already finished."""
        return self.end_date.timetuple().tm_yday

    def clip(self, rows: Sequence[RowT]) -> list[RowT]:
        """Another year's rows, cut off at the same month and day as
        ``end_date``, for a fair comparison.

        Matching on (month, day) rather than the ordinal day-of-year avoids
        misaligning the cutoff when the two years have different lengths (a
        leap year on either side).
        """
        cutoff = (self.end_date.month, self.end_date.day)
        return [row for row in rows if (row.date.month, row.date.day) <= cutoff]
