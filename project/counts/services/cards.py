from dataclasses import dataclass
from statistics import median

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _
from django.utils.translation import pgettext

from ...core.lib.stat_card import Card, EmptyStatCard, StatCard
from .counter_life import CounterLife


def card_total_ever(life: CounterLife) -> Card:
    """On two Tabs on purpose: Overview reads the year against it, History is
    about it."""
    title = _("Total ever")

    if not life.records:
        return EmptyStatCard(title, _("No records"))

    return StatCard(
        title=title,
        value=floatformat(life.rhythm.total_ever, "0g"),
        note=_("since %(year)s") % {"year": life.first_year},
    )


@dataclass(frozen=True)
class OverviewCards:
    life: CounterLife

    @classmethod
    def build(cls, life: CounterLife) -> list[Card]:
        return cls(life)._cards()

    def _cards(self) -> list[Card]:
        return [self._card_year(), card_total_ever(self.life), self._card_gap()]

    def _card_year(self) -> Card:
        title = pgettext("counts card", "This year")

        if not self.life.rhythm.year_records:
            return EmptyStatCard(title, _("No records"))

        return StatCard(title=title, value=floatformat(self.life.year_total, "0g"))

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
    def build(cls, life: CounterLife) -> list[Card]:
        return cls(life)._cards()

    def _cards(self) -> list[Card]:
        return [
            card_total_ever(self.life),
            self._card_years(),
            self._card_median_year(),
        ]

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


@dataclass(frozen=True)
class PeriodicityCards:
    life: CounterLife

    @classmethod
    def build(cls, life: CounterLife) -> list[Card]:
        return cls(life)._cards()

    def _cards(self) -> list[Card]:
        return [self._card_rate(), self._card_typical_gap(), self._card_longest_gap()]

    def _card_rate(self) -> Card:
        title = _("Per year")
        rate = self.life.rhythm.rate

        if not self.life.records:
            return EmptyStatCard(title, _("No records"))

        # one Record spans no time, so it supports no rate — but it is a Record
        if not rate:
            return EmptyStatCard(
                title, _("since %(year)s") % {"year": self.life.first_year}
            )

        return StatCard(
            title=title,
            value=floatformat(rate, "1g"),
            note=_("this year: %(value)s")
            % {"value": floatformat(self.life.rhythm.year_records, "0g")},
            explanation=(_("Records a year, over the counter's whole life"),),
        )

    def _card_typical_gap(self) -> Card:
        title = _("Typical gap")
        rhythm = self.life.rhythm
        typical = rhythm.typical_gap

        if not typical.has_data:
            return EmptyStatCard(title, _("No records"))

        note = ""
        if rhythm.year_median_gap.has_data:
            note = _("this year: %(days)s d.") % {
                "days": floatformat(rhythm.year_median_gap.days, "0g")
            }

        return StatCard(
            title=title,
            value=floatformat(typical.days, "0g"),
            note=note,
            explanation=(_("The median of every gap"),),
        )

    def _card_longest_gap(self) -> Card:
        title = _("Longest gap")
        longest = self.life.rhythm.longest_gap

        if not longest.has_data:
            return EmptyStatCard(title, _("No records"))

        return StatCard(
            title=title,
            value=floatformat(longest.days, "0g"),
            note=longest.label,
        )
