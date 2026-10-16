import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol, TypeVar


class DatedRow(Protocol):
    """Structural, so an app's rows satisfy it without core importing the app."""

    @property
    def date(self) -> date: ...


RowT = TypeVar("RowT", bound=DatedRow)


@dataclass(frozen=True)
class YearBoundary:
    """How far into a year a metric may read: to today while it runs, Dec 31 after;
    the year before only to the same month and day."""

    year: int
    today: date

    @property
    def is_current(self) -> bool:
        return self.year == self.today.year

    @property
    def end_date(self) -> date:
        """Today while the year is running, Dec 31 once it is over."""
        return self.today if self.is_current else date(self.year, 12, 31)

    @property
    def previous_end_date(self) -> date:
        """Feb 29 clamps to Feb 28, the one day with no counterpart a year back."""
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
        return self.end_date.timetuple().tm_yday

    @property
    def weeks_elapsed(self) -> int:
        """Days of a neighbouring ISO year read as this year's first or last week."""
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
        """Matches (month, day), not ordinal day, so leap years keep the cutoff."""
        cutoff = (self.end_date.month, self.end_date.day)
        return [row for row in rows if (row.date.month, row.date.day) <= cutoff]
