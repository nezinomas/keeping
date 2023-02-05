import itertools as it
from dataclasses import dataclass, field
from operator import itemgetter

from django.utils.translation import gettext as _

from ..lib.balance_base import BalanceBase
from ...core.lib.colors import CHART
from ...core.lib.date import current_day
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import PlanCalculateDaySum
from ...savings.models import Saving
from ..lib.day_spending import DaySpending


@dataclass
class MonthServiceData:
    year: int
    month: int

    incomes: list[dict] = \
        field(init=False, default_factory=list)

    expenses: list[dict] = \
        field(init=False, default_factory=list)

    expense_types: list = \
        field(init=False, default_factory=list)

    necessary_expense_types: list = \
        field(init=False, default_factory=list)

    savings: list = \
        field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = list(
            Income.objects
            .sum_by_month(self.year, self.month))

        self.expenses = list(
                Expense.objects
                .sum_by_day_ant_type(self.year, self.month))

        self.expense_types = list(
                ExpenseType.objects
                .items()
                .values_list('title', flat=True)
            )

        self.necessary_expense_types =  \
            ExpenseType.objects \
            .items() \
            .filter(necessary=True) \
            .values_list('title', flat=True)

        self.savings = list(
            Saving.objects
            .sum_by_day(self.year, self.month))


class MonthService():
    def __init__(self,
                 data: MonthServiceData,
                 plans: PlanCalculateDaySum,
                 savings: BalanceBase,
                 spending: DaySpending):
        self._data = data
        self._plans = plans
        self._spending = spending
        self._savings =  savings

    def chart_targets_context(self):
        total_row = self._spending.total_row
        targets = self._plans.targets

        # append savings
        self._append_savings(total_row, self._savings.total)
        self._append_savings(targets, self._plans.savings)

        categories, data_target, data_fact = self._chart_targets(total_row, targets)

        return {
            'categories': categories,
            'target': data_target,
            'targetTitle': _('Plan'),
            'fact': data_fact,
            'factTitle': _('Fact'),
        }

    def chart_expenses_context(self, color: tuple = CHART):
        total_row = self._spending.total_row

        # append savings
        self._append_savings(total_row, self._savings.total)

        return self._chart_expenses(total_row, color)

    def info_context(self):
        fact_incomes = self._data.incomes
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_savings = self._savings.total
        fact_expenses = self._spending.total
        fact_per_day = self._spending.avg_per_day
        fact_balance = fact_incomes - fact_expenses - fact_savings

        plan_incomes = self._plans.incomes
        plan_savings = self._plans.savings
        plan_expenses = plan_incomes - plan_savings
        plan_per_day = self._plans.day_input
        plan_balance = self._plans.remains

        return [
            dict(
                title=_('Incomes'),
                plan=plan_incomes,
                fact=fact_incomes,
                delta=fact_incomes - plan_incomes),
            dict(
                title=_('Expenses'),
                plan=plan_expenses,
                fact=fact_expenses,
                delta=plan_expenses - fact_expenses),
            dict(
                title=_('Savings'),
                plan=plan_savings,
                fact=fact_savings,
                delta=plan_savings - fact_savings),
            dict(
                title=_('Money for a day'),
                plan=plan_per_day,
                fact=fact_per_day,
                delta=plan_per_day - fact_per_day),
            dict(
                title=_('Balance'),
                plan=plan_balance,
                fact=fact_balance,
                delta=fact_balance - plan_balance),
        ]

    def month_table_context(self) -> dict:
        return {
            'day': current_day(self._data.year, self._data.month, False),
            'expenses': it.zip_longest(self._spending.balance,
                                       self._spending.total_column,
                                       self._spending.spending,
                                       self._savings.total_column),
            'expense_types': self._data.expense_types,
            'total': self._spending.total,
            'total_row': self._spending.total_row,
            'total_savings': self._savings.total
        }

    def _chart_expenses(self, total_row: dict, colors: tuple) -> list[dict]:
        data = self._make_chart_data(total_row)

        # add colors
        for key, item in enumerate(data):
            # if colors is shorter then categories
            if key >= len(colors):
                colors *= 2

            item['color'] = colors[key]

        # categories upper case
        for x in data:
            x['name'] = x['name'].upper()

        return data

    def _chart_targets(self,
                      total_row: dict,
                      targets: dict
                      ) -> tuple[list[str], list[float], list[dict]]:

        data = self._make_chart_data(total_row)

        rtn_categories = []
        rtn_data_fact = []
        rtn_data_target = []

        for arr in data:
            category = arr['name']
            target = float(targets.get(category, 0.0))
            fact = float(arr['y'])

            rtn_categories.append(category.upper())
            rtn_data_target.append(target)
            rtn_data_fact.append({'y': fact, 'target': target})

        return (rtn_categories, rtn_data_target, rtn_data_fact)

    def _append_savings(self, data: dict, value: float = 0.0):
        title = _('Savings')

        if isinstance(data, dict):
            value = value or 0.0
            data[title] = value

        return data

    def _make_chart_data(self, data: dict) -> list[dict]:
        rtn = []
        for key, val in data.items():
            rtn.append({'name': key, 'y': val})

        if rtn:
            rtn = sorted(rtn, key=itemgetter('y'), reverse=True)

        return rtn
