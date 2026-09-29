from collections.abc import Sequence
from dataclasses import dataclass

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _
from django.utils.translation import pgettext

from ...core.lib.convert_price import int_cents_to_float
from ...core.lib.stat_card import Card, EmptyStatCard, StatCard
from ..lib.calc_day_sum import DataDto, PlanCalculateDaySum


def _sum(rows: Sequence[dict]) -> int:
    return sum(row["amount"] for row in rows)


def _euro(euro: float) -> str:
    return floatformat(euro, "0g")


@dataclass(frozen=True)
class IncomeCards:
    data: DataDto

    @classmethod
    def build(cls, data: DataDto) -> list[Card]:
        return cls(data)._cards()

    def _cards(self) -> list[Card]:
        this_year = pgettext("plans card", "This year")
        median = _("Monthly median")

        total = _sum(self.data.incomes)
        if not total:
            return [EmptyStatCard(this_year), EmptyStatCard(median)]

        return [
            StatCard(title=this_year, value=_euro(int_cents_to_float(total))),
            self._median(median),
        ]

    def _median(self, title: str) -> Card:
        cents = PlanCalculateDaySum(self.data).incomes_avg["1"]

        return StatCard(title=title, value=_euro(int_cents_to_float(cents)))


@dataclass(frozen=True)
class SavingCards:
    data: DataDto

    @classmethod
    def build(cls, data: DataDto) -> list[Card]:
        return cls(data)._cards()

    def _cards(self) -> list[Card]:
        this_year = pgettext("plans card", "This year")
        share = _("Share of planned incomes")
        per_month = _("Per month")

        total = _sum(self.data.savings)
        if not total:
            return [
                EmptyStatCard(this_year),
                EmptyStatCard(share),
                EmptyStatCard(per_month),
            ]

        return [
            StatCard(title=this_year, value=_euro(int_cents_to_float(total))),
            self._share(share, total),
            StatCard(title=per_month, value=_euro(int_cents_to_float(total) / 12)),
        ]

    def _share(self, title: str, total: int) -> Card:
        incomes = _sum(self.data.incomes)
        if not incomes:
            return EmptyStatCard(title)

        return StatCard(
            title=title, value=floatformat(total / incomes * 100, "0"), unit="%"
        )
