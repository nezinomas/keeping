"""How far apart a Counter's Records are, and nothing else.

Gaps come from ``core.lib.day_stats``, which the Calendar already reads: a Card
and a Calendar tooltip disagreeing about the same date is the day both stop
being believed.
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

    @cached_property
    def gaps(self) -> list[Gap]:
        return [
            Gap(days=span.days, dates=(span.start, span.end))
            for span in Stats(data=list(self.records)).gap_spans()
        ]

    @cached_property
    def typical_gap(self) -> Gap | EmptyGap:
        if not self.gaps:
            return EmptyGap()

        return Gap(days=median(gap.days for gap in self.gaps))

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
