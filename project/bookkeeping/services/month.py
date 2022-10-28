import itertools as it
from dataclasses import dataclass, field
from operator import itemgetter
from typing import Dict, List, Tuple

from django.utils.translation import gettext as _

from ...core.lib.colors import CHART
from ...core.lib.date import current_day, monthname
from ...core.lib.utils import get_value_from_dict as get_val
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import PlanCalculateDaySum, PlanCollectData
from ...savings.models import Saving
from ..lib.day_spending import DaySpending
from ..lib.expense_balance import ExpenseBalance


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
        self.incomes = \
            Income.objects \
            .sum_by_month(self.year, self.month)

        self.expenses = \
            Expense.objects \
            .sum_by_day_ant_type(self.year, self.month)

        self.expense_types = \
            list(
                ExpenseType.objects \
                .items() \
                .values_list('title', flat=True)
            )

        self.necessary_expense_types =  \
            ExpenseType.objects \
            .items() \
            .filter(necessary=True) \
            .values_list('title', flat=True)

        self.savings = \
            Saving.objects \
            .sum_by_day(self.year, self.month)


class MonthService():
    def __init__(self, data: MonthServiceData, plans: PlanCalculateDaySum):
        self._data = data
        self._plans = plans

        self._spending = \
            DaySpending(
                year=self._data.year,
                month=self._data.month,
                expenses=self._data.expenses,
                types=self._data.expense_types,
                necessary=self._data.necessary_expense_types,
                plans=self._plans
            )

        self._savings =  \
            ExpenseBalance.days_of_month(
                self._data.year,
                self._data.month,
                self._data.savings,
                [_('Savings')]
            )

    def chart_targets_context(self):
        types = self._data.expense_types.copy()
        types.append(_('Savings'))

        total_row = self._spending.total_row
        total_row.update({_('Savings'): self._savings.total})

        targets = self._plans.targets(self._data.month)
        targets.update({
            _('Savings'): self._plans.savings.get(monthname(self._data.month), 0.0)})

        categories, data_target, data_fact = self._chart_targets(types, total_row, targets)

        return {
            'categories': categories,
            'target': data_target,
            'targetTitle': _('Plan'),
            'fact': data_fact,
            'factTitle': _('Fact'),
        }

    def chart_expenses_context(self):
        types = self._data.expense_types.copy()
        types.append(_('Savings'))

        total_row = self._spending.total_row
        total_row[_('Savings')] = self._savings.total

        return self._chart_expenses(types, total_row)

    def info_context(self):
        fact_incomes = self._data.incomes
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_savings = self._savings.total
        fact_expenses = self._spending.total
        fact_per_day = self._spending.avg_per_day
        fact_balance = fact_incomes - fact_expenses - fact_savings

        plan_incomes = get_val(self._plans.incomes, self._data.month)
        plan_savings = get_val(self._plans.savings, self._data.month)
        plan_expenses = plan_incomes - plan_savings
        plan_per_day = get_val(self._plans.day_input, self._data.month)
        plan_balance = get_val(self._plans.remains, self._data.month)

        return [{
                'title': _('Incomes'),
                'plan': plan_incomes,
                'fact': fact_incomes,
                'delta': fact_incomes - plan_incomes,
            }, {
                'title': _('Expenses'),
                'plan': plan_expenses,
                'fact': fact_expenses,
                'delta': plan_expenses - fact_expenses,
            }, {
                'title': _('Savings'),
                'plan': plan_savings,
                'fact': fact_savings,
                'delta': plan_savings - fact_savings,
            }, {
                'title': _('Money for a day'),
                'plan': plan_per_day,
                'fact': fact_per_day,
                'delta': plan_per_day - fact_per_day,
            }, {
                'title': _('Balance'),
                'plan': plan_balance,
                'fact': fact_balance,
                'delta': fact_balance - plan_balance,
            },]

    def month_table_context(self) -> Dict:
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

    def _chart_expenses(self, types: List[str], total_row: Dict) -> List[Dict]:
        rtn = []

        if not types:
            return rtn

        # make List[Dict] from types and total_row
        for name in types:
            value = total_row.get(name, 0.0)
            arr = {'name': name.upper(), 'y': value}
            rtn.append(arr)

        # sort List[Dict] by y
        rtn = sorted(rtn, key=itemgetter('y'), reverse=True)

        # add to List[Dict] colors
        for key, arr in enumerate(rtn):
            rtn[key]['color'] = CHART[key]

        return rtn

    def _chart_targets(self,
                      types: List[str],
                      total_row: Dict,
                      targets: Dict
                      ) -> Tuple[List[str], List[float], List[Dict]]:
        tmp = []

        # make List[Dict] from types and total_row
        for name in types:
            value = total_row.get(name, 0.0)
            arr = {'name': name, 'y': value}
            tmp.append(arr)

        # sort List[Dict] by y
        tmp = sorted(tmp, key=itemgetter('y'), reverse=True)

        rtn_categories = []
        rtn_data_fact = []
        rtn_data_target = []

        for arr in tmp:
            category = arr['name']
            target = float(targets.get(category, 0.0))
            fact = float(arr['y'])

            rtn_categories.append(category.upper())
            rtn_data_target.append(target)
            rtn_data_fact.append({'y': fact, 'target': target})

        return (rtn_categories, rtn_data_target, rtn_data_fact)
