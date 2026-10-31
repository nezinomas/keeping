from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _
from django.utils.translation import ngettext, pgettext

from .chart_months import ChartMonths
from .convert_price import int_cents_to_float
from .money_cells import amount, share
from .stat_card import Card, EmptyStatCard, StatCard
from .year_boundary import YearBoundary


class SpanReads(Protocol):
    def sum_by_between(self, field: str, start: date, end: date) -> Iterable[dict]: ...

    def sum_by_month_between(self, start: date, end: date) -> Iterable[dict]: ...


def _sum(rows: Sequence[dict]) -> int:
    return sum(row["sum"] for row in rows)


@dataclass(frozen=True)
class Overview:
    cards: list[Card]
    chart: dict

    @classmethod
    def build(
        cls,
        service: SpanReads,
        field: str,
        boundary: YearBoundary,
        largest_type_explanation: str,
    ) -> "Overview":
        return cls(
            cards=OverviewCards.build(
                list(service.sum_by_between(field, *boundary.span)),
                list(service.sum_by_between(field, *boundary.previous_span)),
                boundary,
                largest_type_explanation,
            ),
            chart=ChartMonths.build(
                list(service.sum_by_month_between(*boundary.span)),
                list(service.sum_by_month_between(*boundary.previous_span)),
                boundary,
            ),
        )


@dataclass(frozen=True)
class OverviewCards:
    year: Sequence[dict]
    last_year: Sequence[dict]
    boundary: YearBoundary
    largest_type_explanation: str

    @classmethod
    def build(
        cls,
        year: Sequence[dict],
        last_year: Sequence[dict],
        boundary: YearBoundary,
        largest_type_explanation: str,
    ) -> list[Card]:
        return cls(year, last_year, boundary, largest_type_explanation)._cards()

    def _cards(self) -> list[Card]:
        this_year = pgettext("overview card", "This year")
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
            note = _("Last year %(amount)s") % {"amount": amount(last_year)}

        return StatCard(title=title, value=amount(total), note=note)

    def _per_month(self, title: str, total: int) -> Card:
        # the Year boundary, never 12: a running year has not reached every month
        months = self.boundary.end_date.month

        return StatCard(
            title=title,
            value=floatformat(int_cents_to_float(total) / months, "0g"),
            note=ngettext("%(count)s month", "%(count)s months", months)
            % {"count": months},
            explanation=(_("The year's total divided by the months it has reached"),),
        )

    def _largest_type(self, title: str, total: int) -> Card:
        largest = max(self.year, key=lambda row: row["sum"])

        return StatCard(
            title=title,
            value=largest["title"],
            note=_("%(share)s of the year's total")
            % {"share": share(largest["sum"], total)},
            explanation=(self.largest_type_explanation,),
        )
