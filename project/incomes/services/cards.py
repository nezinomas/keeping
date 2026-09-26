from collections.abc import Sequence
from dataclasses import dataclass

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _
from django.utils.translation import ngettext, pgettext

from ...core.lib.convert_price import int_cents_to_float
from ...core.lib.stat_card import Card, EmptyStatCard, StatCard
from ...core.lib.year_boundary import YearBoundary


def _sum(rows: Sequence[dict]) -> int:
    return sum(row["sum"] for row in rows)


def _euro(euro: float) -> str:
    return floatformat(euro, "2g")


@dataclass(frozen=True)
class OverviewCards:
    year: Sequence[dict]
    last_year: Sequence[dict]
    boundary: YearBoundary

    @classmethod
    def build(
        cls, year: Sequence[dict], last_year: Sequence[dict], boundary: YearBoundary
    ) -> list[Card]:
        return cls(year, last_year, boundary)._cards()

    def _cards(self) -> list[Card]:
        this_year = pgettext("counts card", "This year")
        per_month = _("Per month")
        largest_type = _("Largest type")

        total = _sum(self.year)

        if not total:
            return [
                EmptyStatCard(title) for title in (this_year, per_month, largest_type)
            ]

        return [
            self._this_year(this_year, total),
            self._per_month(per_month, total),
            self._largest_type(largest_type, total),
        ]

    def _this_year(self, title: str, total: int) -> Card:
        last_year = _sum(self.last_year)
        note = ""

        if last_year:
            note = _("Last year %(amount)s") % {
                "amount": _euro(int_cents_to_float(last_year))
            }

        return StatCard(title=title, value=_euro(int_cents_to_float(total)), note=note)

    def _per_month(self, title: str, total: int) -> Card:
        # the Year boundary, never 12: a running year has not reached every month
        months = self.boundary.end_date.month

        return StatCard(
            title=title,
            value=_euro(int_cents_to_float(total) / months),
            note=ngettext("%(count)s month", "%(count)s months", months)
            % {"count": months},
            explanation=(_("The year's total divided by the months it has reached"),),
        )

    def _largest_type(self, title: str, total: int) -> Card:
        largest = max(self.year, key=lambda row: row["sum"])
        share = floatformat(largest["sum"] / total * 100, "0")

        return StatCard(
            title=title,
            value=largest["title"],
            note=_("%(share)s%% of the year's total") % {"share": share},
            explanation=(_("The income type with the biggest share of this year"),),
        )
