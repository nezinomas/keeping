"""How far apart a Counter's Records are, and nothing else.

Gaps come from ``core.lib.day_stats`` rather than being re-derived here, because
a Card and a Calendar tooltip disagreeing about one date is the day both stop
being believed.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from functools import cached_property
from statistics import median

from ...core.lib.day_stats import Stats

DAYS_A_YEAR = 365.25
GAP_BINS = 8


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


@dataclass(frozen=True)
class GapBin:
    low: int
    high: int
    count: int

    @property
    def label(self) -> str:
        return str(self.low) if self.low == self.high else f"{self.low}–{self.high}"


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

    @cached_property
    def gap_distribution(self) -> list[GapBin]:
        days = sorted(int(gap.days) for gap in self.gaps)

        if not days:
            return []

        edges = self._bin_edges(days)

        return [
            GapBin(
                low=low,
                high=high - 1,
                count=sum(1 for day in days if low <= day < high),
            )
            for low, high in zip(edges, edges[1:], strict=False)
        ]

    @staticmethod
    def _bin_edges(days: list[int]) -> list[int]:
        low, high = days[0], days[-1]

        if low == high:
            return [low, high + 1]

        # geometric, because a gap is read against the ones around it rather than
        # on an absolute scale: equal widths spend most of the axis on a tail
        start = math.log(max(low, 1))
        step = (math.log(high + 1) - start) / GAP_BINS
        raw = [round(math.exp(start + step * i)) for i in range(GAP_BINS + 1)]
        raw[0], raw[-1] = low, high + 1

        edges = []
        for edge in raw:
            if not edges or edge > edges[-1]:
                edges.append(edge)

        return edges

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
