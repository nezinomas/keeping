from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol, TypeVar


class DatedRow(Protocol):
    """Any row carrying the calendar date it was recorded on.

    Structural on purpose: the row types belong to the apps, so an app's rows
    satisfy this without core importing anything from an app.
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
        first = records[0].date.year if records else None
        return cls.for_year(first, today)

    @classmethod
    def for_year(
        cls, year: int | None = None, today: date | None = None
    ) -> "YearBoundary":
        """The year the caller already knows, falling back to today's year."""
        today = today or date.today()
        return cls(year=year or today.year, today=today)

    @property
    def is_current(self) -> bool:
        """Whether this is the year running now, as opposed to one already
        finished or one not yet begun."""
        return self.year == self.today.year

    @property
    def end_date(self) -> date:
        """Today while the year is running, Dec 31 once it is over."""
        return self.today if self.is_current else date(self.year, 12, 31)

    @property
    def days_elapsed(self) -> int:
        """Days of the year covered — day-of-year today, 365 or 366 for a year
        already finished."""
        return self.end_date.timetuple().tm_yday

    @property
    def weeks_elapsed(self) -> int:
        """ISO weeks the year has reached — this week's number today, the whole
        year's 52 or 53 once it is over.

        Dec 28 always falls in its own year's last ISO week, which is what makes
        it the way to ask how many weeks a year has. The turn of the year is the
        awkward part: early January can belong to the previous ISO year
        (2027-01-01 is week 53 of 2026) and late December to the next one
        (2024-12-30 is week 1 of 2025). Both read here as the week of *this*
        year they fall in, so a two-day-old year is never divided by 53.
        """
        weeks_in_year = date(self.year, 12, 28).isocalendar()[1]
        if self.year != self.today.year:
            return weeks_in_year

        iso = self.today.isocalendar()
        if iso.year < self.year:
            return 1
        if iso.year > self.year:
            return weeks_in_year
        return iso.week

    def clip(self, rows: Sequence[RowT]) -> list[RowT]:
        """Another year's rows, cut off at the same month and day as
        ``end_date``, for a fair comparison.

        Matching on (month, day) rather than the ordinal day-of-year avoids
        misaligning the cutoff when the two years have different lengths (a
        leap year on either side).
        """
        cutoff = (self.end_date.month, self.end_date.day)
        return [row for row in rows if (row.date.month, row.date.day) <= cutoff]
