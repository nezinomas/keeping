from dataclasses import dataclass

from django.utils.translation import gettext as _

from ..lib.calc_day_sum import MONTH_NUMS, WITHIN, PlanCalculateDaySum


def _values(row: dict) -> list:
    return [row[month] for month in MONTH_NUMS]


@dataclass(frozen=True)
class CalculationRow:
    label: str
    words: str
    values: list
    part: bool
    states: list[str]

    @property
    def cells(self):
        return list(zip(self.values, self.states))


@dataclass(frozen=True)
class CalculationBlock:
    title: str
    rows: list[CalculationRow]


@dataclass(frozen=True)
class Calculations:
    day_sum: PlanCalculateDaySum

    @classmethod
    def build(cls, day_sum: PlanCalculateDaySum) -> list[CalculationBlock]:
        return cls(day_sum)._blocks()

    def _blocks(self) -> list[CalculationBlock]:
        return [self._spend_block(), self._check_block()]

    def _row(self, label, words, row, part=False, states=()):
        row_states = [WITHIN] * 12
        if states:
            row_states = list(states)

        return CalculationRow(
            label=label,
            words=words,
            values=_values(row),
            part=part,
            states=row_states,
        )

    def _spend_block(self) -> CalculationBlock:
        day_sum = self.day_sum
        day_states = _values(day_sum.day_plan_states())

        rows = [
            self._row(
                _("Incomes"),
                _("median of the monthly income plans"),
                day_sum.incomes_avg,
            ),
            self._row(
                _("Necessary expenses"),
                _("expense plans of necessary types"),
                day_sum.db_expenses_necessary,
                part=True,
            ),
            self._row(
                _("Additional necessary expenses"), "", day_sum.necessary, part=True
            ),
            self._row(_("Savings"), "", day_sum.savings, part=True),
            self._row(
                _("Necessary expenses and savings"),
                _("= necessary + additional + savings"),
                day_sum.expenses_necessary,
            ),
            self._row(
                _("Free money"),
                _("= Incomes − Necessary expenses and savings"),
                day_sum.expenses_free,
            ),
            self._row(
                _("Sum per day"), _("= Free money ÷ days in month"), day_sum.day_calced
            ),
            self._row(
                _("Day plan"),
                _("yours, from the Sum per day table"),
                day_sum.day_input,
                states=day_states,
            ),
            # no states: the Day plan row already marks the months that do not fit
            self._row(
                _("Residual"), _("= Free money − Day plan × days"), day_sum.remains
            ),
        ]

        return CalculationBlock(title=_("How much can I spend per day"), rows=rows)

    def _check_block(self) -> CalculationBlock:
        day_sum = self.day_sum

        rows = [
            self._row(
                _("Everyday expenses as planned"),
                _("expense plans of other types"),
                day_sum.expenses_regular,
            ),
            self._row(
                _("Full expenses"),
                _("= Necessary expenses and savings + Everyday expenses"),
                day_sum.expenses_full,
            ),
            self._row(
                _("Incomes − full expenses"),
                _("= Incomes − Full expenses"),
                day_sum.expenses_remains,
            ),
        ]

        return CalculationBlock(title=_("Check: do the expense plans fit"), rows=rows)
