import itertools as it
from operator import itemgetter
from typing import Dict, List, Tuple

from django.utils.translation import gettext as _

from ...core.lib.colors import CHART
from ...core.lib.date import current_day, monthname
from ...core.lib.utils import get_value_from_dict as get_val
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import PlanCalculateDaySum
from ...savings.models import Saving
from ..lib.day_spending import DaySpending
from ..lib.expense_summary import ExpenseBase
from .common import expense_types


class MonthService():
    def __init__(self, year, month):
        self._year = year
        self._month = month

        self._expense_types = expense_types()
        self._plans = PlanCalculateDaySum(year)
        self._spending = self._day_spending_object(year, month, self._plans)

        self._savings = self._saving_object(year, month)

    def _saving_object(self, year: int, month: int) -> ExpenseBase:
        qs_savings = Saving.objects.sum_by_day(year, month)

        return \
            ExpenseBase.days_of_month(
                year,
                month,
                qs_savings,
                [_('Savings')]
            )

    def _day_spending_object(self, year: int, month: int, plans: PlanCalculateDaySum) -> DaySpending:
        qs_expenses = Expense.objects.sum_by_day_ant_type(year, month)

        return \
            DaySpending(
                year=year,
                month=month,
                expenses=qs_expenses,
                types=self._expense_types,
                necessary=self._necessary_expense_types(),
                plans=plans
            )

    def chart_targets_context(self):
        types = self._expense_types.copy()
        types.append(_('Savings'))

        total_row = self._spending.total_row
        total_row.update({_('Savings'): self._savings.total})

        targets = self._plans.targets(self._month)
        targets.update({
            _('Savings'): self._plans.savings.get(monthname(self._month), 0.0)})

        categories, data_target, data_fact = self._chart_targets(types, total_row, targets)

        return {
            'chart_targets_categories': categories,
            'chart_targets_data_target': data_target,
            'chart_targets_data_fact': data_fact,
        }

    def chart_expenses_context(self):
        types = self._expense_types.copy()
        types.append(_('Savings'))

        total_row = self._spending.total_row
        total_row[_('Savings')] = self._savings.total

        return {
            'expenses': self._chart_expenses(types, total_row)
        }

    def info_context(self):
        fact_incomes = Income.objects.sum_by_month(self._year, self._month)
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_savings = self._savings.total
        fact_expenses = self._spending.total
        fact_per_day = self._spending.avg_per_day
        fact_balance = fact_incomes - fact_expenses - fact_savings

        plan_incomes = get_val(self._plans.incomes, self._month)
        plan_savings = get_val(self._plans.savings, self._month)
        plan_expenses = plan_incomes - plan_savings
        plan_per_day = get_val(self._plans.day_input, self._month)
        plan_balance = get_val(self._plans.remains, self._month)

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
            'day': current_day(self._year, self._month, False),
            'expenses': it.zip_longest(self._spending.balance,
                                       self._spending.total_column,
                                       self._spending.spending,
                                       self._savings.total_column),
            'expense_types': self._expense_types,
            'total': self._spending.total,
            'total_row': self._spending.total_row,
            'total_savings': float(self._savings.total)
        }

    def _necessary_expense_types(self, *args: str) -> List[str]:
        qs = list(
            ExpenseType
            .objects
            .items()
            .filter(necessary=True)
            .values_list('title', flat=True)
        )

        list(qs.append(x) for x in args)

        qs.sort()

        return qs

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
