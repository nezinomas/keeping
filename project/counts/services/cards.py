from collections import Counter
from dataclasses import dataclass
from statistics import median

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _
from django.utils.translation import pgettext

from ...core.lib.stat_card import Card, EmptyStatCard, StatCard
from ...core.lib.year_boundary import YearBoundary
from ...users.models import User
from ..lib.rhythm import Rhythm
from .model_services import CountModelService


@dataclass(frozen=True)
class CounterLife:
    """Every Record a Counter holds, read once and shared by both card rows."""

    records: list[dict]
    boundary: YearBoundary

    @classmethod
    def read(cls, user: User, count_type: str) -> "CounterLife":
        boundary = YearBoundary.for_year(user.year)
        records = list(
            CountModelService(user)
            .items(count_type=count_type)
            .values("date", "quantity")
        )

        return cls(records=records, boundary=boundary)

    @property
    def rhythm(self) -> Rhythm:
        return Rhythm(self.records, today=self.boundary.today)

    @property
    def year_total(self) -> float:
        return float(
            sum(
                record["quantity"]
                for record in self.records
                if record["date"].year == self.boundary.year
            )
        )

    @property
    def totals_by_year(self) -> dict[int, float]:
        totals = Counter()
        for record in self.records:
            totals[record["date"].year] += record["quantity"]

        return dict(sorted(totals.items()))

    @property
    def first_year(self) -> int:
        return min(self.totals_by_year, default=0)

    def since_note(self) -> str:
        return _("since %(year)s") % {"year": self.first_year}


@dataclass(frozen=True)
class OverviewCards:
    life: CounterLife

    @classmethod
    def build(cls, user: User, count_type: str) -> list[Card]:
        return cls(CounterLife.read(user, count_type))._cards()

    def _cards(self) -> list[Card]:
        return [self._card_year(), self._card_total(), self._card_gap()]

    def _card_year(self) -> Card:
        title = pgettext("counts card", "This year")

        if not self.life.year_total:
            return EmptyStatCard(title, _("No records"))

        return StatCard(title=title, value=floatformat(self.life.year_total, "0g"))

    def _card_total(self) -> Card:
        title = _("Total ever")
        total = self.life.rhythm.total_ever

        if not total:
            return EmptyStatCard(title, _("No records"))

        return StatCard(
            title=title,
            value=floatformat(total, "0g"),
            note=self.life.since_note(),
        )

    def _card_gap(self) -> Card:
        title = _("Gap")
        rhythm = self.life.rhythm
        typical = rhythm.typical_gap
        note = ""

        if typical.has_data:
            note = _("typically %(days)s d.") % {
                "days": floatformat(typical.days, "0g")
            }

        if not self.life.boundary.is_current or not self.life.records:
            return EmptyStatCard(title, note or _("No records"))

        return StatCard(
            title=title,
            value=floatformat(rhythm.current_gap, "0g"),
            note=note,
            explanation=(_("Days since the last record"),),
        )


@dataclass(frozen=True)
class HistoryCards:
    life: CounterLife

    @classmethod
    def build(cls, user: User, count_type: str) -> list[Card]:
        return cls(CounterLife.read(user, count_type))._cards()

    def _cards(self) -> list[Card]:
        return [self._card_total(), self._card_years(), self._card_median_year()]

    def _card_total(self) -> Card:
        return OverviewCards(self.life)._card_total()

    def _card_years(self) -> Card:
        title = pgettext("counts card", "Years")
        years = list(self.life.totals_by_year)
        explanation = (_("Years with at least one record"),)

        if not years:
            return EmptyStatCard(title, _("No records"))

        span = f"{years[0]}" if len(years) == 1 else f"{years[0]}–{years[-1]}"

        return StatCard(
            title=title,
            value=floatformat(len(years), "0g"),
            note=span,
            explanation=explanation,
        )

    def _card_median_year(self) -> Card:
        title = _("Median year")
        explanation = (_("The median of the yearly totals"),)
        totals = [
            total
            for year, total in self.life.totals_by_year.items()
            if year != self.life.boundary.year or not self.life.boundary.is_current
        ]

        if not totals:
            return EmptyStatCard(title, _("No records"))

        note = _("from %(low)s to %(high)s") % {
            "low": floatformat(min(totals), "0g"),
            "high": floatformat(max(totals), "0g"),
        }

        return StatCard(
            title=title,
            value=floatformat(median(totals), "0g"),
            note=note,
            explanation=explanation,
        )
