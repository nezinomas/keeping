from collections.abc import Sequence
from dataclasses import dataclass

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _
from django.utils.translation import pgettext

from ...core.lib.convert_price import int_cents_to_float
from ...core.lib.stat_card import (
    HIGH,
    NEUTRAL,
    Card,
    EmptyStatCard,
    LevelStatCard,
    StatCard,
)
from ..lib.calc_day_sum import OVER, DataDto, PlanCalculateDaySum


def _sum(rows: Sequence[dict]) -> int:
    return sum(row["amount"] for row in rows)


def _euro(euro: float) -> str:
    return floatformat(euro, "0g")


def _euro_cents(cents: int) -> str:
    return floatformat(int_cents_to_float(cents), "2g")


@dataclass(frozen=True)
class IncomeCards:
    data: DataDto

    @classmethod
    def build(cls, data: DataDto) -> list[Card]:
        return cls(data)._cards()

    def _cards(self) -> list[Card]:
        per_year = pgettext("plans card", "Per year")
        median = _("Monthly median")

        total = _sum(self.data.incomes)
        if not total:
            return [EmptyStatCard(per_year), EmptyStatCard(median)]

        return [
            StatCard(title=per_year, value=_euro(int_cents_to_float(total))),
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
        per_year = pgettext("plans card", "Per year")
        share = _("Share of planned incomes")
        per_month = _("Per month")

        total = _sum(self.data.savings)
        if not total:
            return [
                EmptyStatCard(per_year),
                EmptyStatCard(share),
                EmptyStatCard(per_month),
            ]

        return [
            StatCard(title=per_year, value=_euro(int_cents_to_float(total))),
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


@dataclass(frozen=True)
class ExpenseCards:
    data: DataDto

    @classmethod
    def build(cls, data: DataDto) -> list[Card]:
        return cls(data)._cards()

    def _cards(self) -> list[Card]:
        per_year = pgettext("plans card", "Per year")
        necessary = pgettext("plans card", "Necessary")
        everyday = pgettext("plans card", "Everyday")
        per_month = _("Per month")

        regular = _sum(self.data.expenses_regular)
        total = regular + _sum(self.data.expenses_necessary) + _sum(self.data.necessary)
        if not total:
            return [
                EmptyStatCard(per_year),
                EmptyStatCard(necessary),
                EmptyStatCard(everyday),
                EmptyStatCard(per_month),
            ]

        return [
            StatCard(title=per_year, value=_euro(int_cents_to_float(total))),
            self._necessary(necessary),
            self._everyday(everyday, regular),
            StatCard(title=per_month, value=_euro(int_cents_to_float(total) / 12)),
        ]

    def _everyday(self, title: str, regular: int) -> Card:
        if not regular:
            return EmptyStatCard(title)

        return StatCard(title=title, value=_euro(int_cents_to_float(regular)))

    def _necessary(self, title: str) -> Card:
        calc = PlanCalculateDaySum(self.data)
        cents = sum(calc.db_expenses_necessary.values()) + sum(calc.necessary.values())

        return StatCard(title=title, value=_euro(int_cents_to_float(cents)))


@dataclass(frozen=True)
class DayCards:
    data: DataDto
    month: int

    @classmethod
    def build(cls, data: DataDto, month: int) -> list[Card]:
        return cls(data, month)._cards()

    def _cards(self) -> list[Card]:
        sum_per_day = _("Sum per day this month")
        day_plan = _("Day plan this month")

        calc = PlanCalculateDaySum(self.data)
        month = str(self.month)

        return [
            self._sum_per_day(sum_per_day, calc, month),
            self._day_plan(day_plan, calc, month),
        ]

    def _sum_per_day(self, title: str, calc: PlanCalculateDaySum, month: str) -> Card:
        if not _sum(self.data.incomes):
            return EmptyStatCard(title)

        return StatCard(title=title, value=_euro_cents(calc.day_calced[month]))

    def _day_plan(self, title: str, calc: PlanCalculateDaySum, month: str) -> Card:
        cents = calc.day_input[month]
        if not cents:
            return EmptyStatCard(title)

        state = HIGH if calc.day_plan_states()[month] == OVER else NEUTRAL
        return LevelStatCard(title=title, value=_euro_cents(cents), state=state)
