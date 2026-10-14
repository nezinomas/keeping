import calendar
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
    def previous_end_date(self) -> date:
        """The same point in the year before — how far a baseline may read.

        Feb 29 clamps onto Feb 28, which is the only day of the year that has no
        counterpart a year back.
        """
        end = self.end_date
        day = min(end.day, calendar.monthrange(self.year - 1, end.month)[1])

        return date(self.year - 1, end.month, day)

    @property
    def span(self) -> tuple[date, date]:
        return date(self.year, 1, 1), self.end_date

    @property
    def previous_span(self) -> tuple[date, date]:
        return date(self.year - 1, 1, 1), self.previous_end_date

    @property
    def days_elapsed(self) -> int:
        """Days of the year covered — day-of-year today, 365 or 366 for a year
        already finished."""
        return self.end_date.timetuple().tm_yday

    @property
    def weeks_elapsed(self) -> int:
        """ISO weeks the year has reached, 52 or 53 once it is over.

        Days of a neighbouring ISO year read as this year's first or last week.
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
