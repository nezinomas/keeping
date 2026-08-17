from collections import Counter
from dataclasses import dataclass
from datetime import date
from functools import cached_property

from ...core.lib.year_boundary import YearBoundary
from ...users.models import User
from ..lib.rhythm import Rhythm
from .model_services import CountModelService


@dataclass
class CounterLife:
    """Every Record a Counter holds, read once and shared by everything a Tab
    draws — the Cards and the charts read the same list or they disagree."""

    user: User
    count_type: str
    records: list[dict]
    boundary: YearBoundary

    @classmethod
    def read(cls, user: User, count_type: str) -> "CounterLife":
        return cls(
            user=user,
            count_type=count_type,
            records=list(
                CountModelService(user)
                .items(count_type=count_type)
                .values("date", "quantity")
            ),
            boundary=YearBoundary.for_year(user.year),
        )

    @cached_property
    def rhythm(self) -> Rhythm:
        return Rhythm(self.records, today=self.boundary.today, year=self.boundary.year)

    @cached_property
    def year_total(self) -> float:
        return float(
            sum(
                record["quantity"]
                for record in self.records
                if record["date"].year == self.boundary.year
            )
        )

    @cached_property
    def totals_by_year(self) -> dict[int, float]:
        totals = Counter()
        for record in self.records:
            totals[record["date"].year] += record["quantity"]

        return dict(sorted(totals.items()))

    @property
    def first_year(self) -> int:
        return min(self.totals_by_year, default=0)

    @property
    def span(self) -> str:
        """A chart that pools must caption the years it pooled."""
        years = list(self.totals_by_year)

        if not years:
            return str(self.boundary.year)

        return str(years[0]) if len(years) == 1 else f"{years[0]}–{years[-1]}"

    @cached_property
    def past_latest(self) -> date | None:
        """The last Record before the year on view, so the year's first Gap
        reaches back into the year before it."""
        past = [
            record["date"]
            for record in self.records
            if record["date"].year < self.boundary.year
        ]

        return max(past) if past else None
