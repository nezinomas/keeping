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
from ..lib.calc_day_sum import CalcRow, DataDto, InputRow, PlanCalculateDaySum
from ..lib.month_states import OVER

MONTHS = 12


def _sum(rows: Sequence[dict]) -> int:
    return sum(row["amount"] for row in rows)


def _whole_euros(cents: float) -> str:
    return floatformat(int_cents_to_float(cents), "0g")


def _euros_and_cents(cents: int) -> str:
    return floatformat(int_cents_to_float(cents), "2g")


def _amount_card(title: str, cents: float) -> Card:
    if not cents:
        return EmptyStatCard(title)

    return StatCard(title=title, value=_whole_euros(cents))


def _year_card(total: int) -> Card:
    return _amount_card(pgettext("plans card", "Per year"), total)


def _month_card(total: int) -> Card:
    return _amount_card(_("Per month"), total / MONTHS)


@dataclass(frozen=True)
class IncomeCards:
    data: DataDto

    @classmethod
    def build(cls, data: DataDto) -> list[Card]:
        return cls(data)._cards()

    def _cards(self) -> list[Card]:
        total = _sum(self.data.incomes)

        return [_year_card(total), self._median(total)]

    def _median(self, total: int) -> Card:
        title = _("Monthly median")
        if not total:
            return EmptyStatCard(title)

        cents = PlanCalculateDaySum(self.data).cell(CalcRow.INCOMES_AVG, 1)

        return StatCard(title=title, value=_whole_euros(cents))


@dataclass(frozen=True)
class SavingCards:
    data: DataDto

    @classmethod
    def build(cls, data: DataDto) -> list[Card]:
        return cls(data)._cards()

    def _cards(self) -> list[Card]:
        total = _sum(self.data.savings)

        return [_year_card(total), self._share(total), _month_card(total)]

    def _share(self, total: int) -> Card:
        title = _("Share of planned incomes")
        incomes = _sum(self.data.incomes)
        if not total or not incomes:
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
        regular = _sum(self.data.expenses_regular)
        necessary = _sum(self.data.expenses_necessary) + _sum(self.data.necessary)
        total = regular + necessary

        return [
            _year_card(total),
            _amount_card(pgettext("plans card", "Necessary"), necessary),
            _amount_card(pgettext("plans card", "Everyday"), regular),
            _month_card(total),
        ]


@dataclass(frozen=True)
class DayCards:
    calc: PlanCalculateDaySum
    month: int

    @classmethod
    def build(cls, calc: PlanCalculateDaySum, month: int) -> list[Card]:
        return cls(calc, month)._cards()

    def _cards(self) -> list[Card]:
        return [
            self._sum_per_day(_("Sum per day this month")),
            self._day_plan(_("Day plan this month")),
        ]

    def _sum_per_day(self, title: str) -> Card:
        if not sum(self.calc.row(InputRow.INCOMES).values()):
            return EmptyStatCard(title)

        cents = self.calc.cell(CalcRow.SUM_PER_DAY, self.month)
        return StatCard(title=title, value=_euros_and_cents(cents))

    def _day_plan(self, title: str) -> Card:
        cents = self.calc.cell(InputRow.DAY_PLAN, self.month)
        if not cents:
            return EmptyStatCard(title)

        over = self.calc.day_plan_states()[str(self.month)] == OVER
        state = HIGH if over else NEUTRAL
        return LevelStatCard(title=title, value=_euros_and_cents(cents), state=state)
