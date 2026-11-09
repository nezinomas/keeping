import calendar
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol, TypeVar


class DatedRow(Protocol):
    """Structural, so an app's rows satisfy it without core importing the app."""

    @property
    def date(self) -> date: ...


RowT = TypeVar("RowT", bound=DatedRow)


def _same_month_and_day(day: date, year: int) -> date:
    """Feb 29 folds into Feb 28, the one day a common year has no counterpart for."""
    last = calendar.monthrange(year, day.month)[1]
    return date(year, day.month, min(day.day, last))


@dataclass(frozen=True)
class YearBoundary:
    """How far into a year a metric may read: to today while it runs, Dec 31 after,
    nothing yet for a Coming year; the year before only to the same month and day,
    today's for a Coming year."""

    year: int
    today: date

    @property
    def is_current(self) -> bool:
        return self.year == self.today.year

    @property
    def is_coming(self) -> bool:
        return self.year > self.today.year

    @property
    def end_date(self) -> date:
        """Today while the year is running, Dec 31 once it is over or not begun."""
        return self.today if self.is_current else date(self.year, 12, 31)

    @property
    def last_day_reached(self) -> date:
        """The day before Jan 1 for a Coming year, so a range up to it is empty."""
        if self.is_coming:
            return date(self.year, 1, 1) - timedelta(days=1)

        return self.end_date

    @property
    def _year_before_reads_to(self) -> date:
        """The month and day the year before is read to."""
        if self.is_coming:
            return self.today

        return self.end_date

    @property
    def previous_end_date(self) -> date:
        return _same_month_and_day(self._year_before_reads_to, self.year - 1)

    def this_years_day(self, day: date) -> date:
        """A day of the year before, moved to this year's same month and day."""
        return _same_month_and_day(day, self.year)

    @property
    def span(self) -> tuple[date, date]:
        return date(self.year, 1, 1), self.end_date

    @property
    def previous_span(self) -> tuple[date, date]:
        return date(self.year - 1, 1, 1), self.previous_end_date

    @property
    def days_elapsed(self) -> int:
        return (self.last_day_reached - date(self.year, 1, 1)).days + 1

    @property
    def weeks_elapsed(self) -> int:
        """Days of a neighbouring ISO year read as this year's first or last week."""
        if self.is_coming:
            return 0

        weeks_in_year = date(self.year, 12, 28).isocalendar()[1]
        if not self.is_current:
            return weeks_in_year

        iso = self.today.isocalendar()
        if iso.year < self.year:
            return 1
        if iso.year > self.year:
            return weeks_in_year
        return iso.week

    @property
    def months_elapsed(self) -> int:
        if self.is_coming:
            return 0

        return self.end_date.month

    def clip(self, rows: Sequence[RowT]) -> list[RowT]:
        """Matches (month, day), not ordinal day, so leap years keep the cutoff."""
        cutoff = (self._year_before_reads_to.month, self._year_before_reads_to.day)
        return [row for row in rows if (row.date.month, row.date.day) <= cutoff]
