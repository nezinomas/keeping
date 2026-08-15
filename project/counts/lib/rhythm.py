"""How far apart a Counter's Records are, and nothing else.

Gaps come from ``core.lib.day_stats``, which the Calendar already reads: a Card
and a Calendar tooltip disagreeing about one date is the day both stop being
believed. The Current gap is open where the rest are closed, so it enters none
of them.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from functools import cached_property
from statistics import median

from ...core.lib.day_stats import Stats

DAYS_A_YEAR = 365.25


@dataclass(frozen=True)
class Gap:
    days: float
    dates: tuple[date, ...] = ()

    has_data = True

    @property
    def label(self) -> str:
        return " → ".join(day.strftime("%Y-%m-%d") for day in self.dates)


class EmptyGap:
    days = 0
    dates = ()
    label = ""
    has_data = False


@dataclass
class Rhythm:
    records: Sequence[dict] = ()
    today: date = field(default_factory=date.today)
    year: int = 0

    @cached_property
    def gaps(self) -> list[Gap]:
        return [
            Gap(days=span.days, dates=(span.start, span.end))
            for span in Stats(data=list(self.records)).gap_spans()
        ]

    @cached_property
    def year_gaps(self) -> list[Gap]:
        """A year's Gaps reach back to the last Record of the year before."""
        return [gap for gap in self.gaps if gap.dates[-1].year == self.year]

    # the two medians read different sets on purpose: a year holding two Gaps
    # has no median worth the name, where thirteen years hold thirty-six
    @cached_property
    def typical_gap(self) -> Gap | EmptyGap:
        return self._median(self.gaps)

    @cached_property
    def year_median_gap(self) -> Gap | EmptyGap:
        return self._median(self.year_gaps)

    @cached_property
    def longest_gap(self) -> Gap | EmptyGap:
        if not self.gaps:
            return EmptyGap()

        return max(self.gaps, key=lambda gap: gap.days)

    @property
    def year_records(self) -> int:
        return sum(1 for record in self.records if record["date"].year == self.year)

    @staticmethod
    def _median(gaps: list[Gap]) -> Gap | EmptyGap:
        if not gaps:
            return EmptyGap()

        return Gap(days=median(gap.days for gap in gaps))

    @property
    def total_ever(self) -> float:
        return float(sum(record["quantity"] for record in self.records))

    @property
    def rate(self) -> float:
        rate = 0.0

        if span := self._span_days:
            rate = len(self.records) * DAYS_A_YEAR / span

        return rate

    @property
    def current_gap(self) -> int:
        gap = 0

        if self._dates:
            gap = (self.today - max(self._dates)).days

        return gap

    @property
    def _dates(self) -> list[date]:
        return [record["date"] for record in self.records]

    @property
    def _span_days(self) -> int:
        dates = self._dates

        return (max(dates) - min(dates)).days if dates else 0
