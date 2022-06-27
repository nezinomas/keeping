import itertools as it
from operator import itemgetter
from typing import Dict, List, Tuple

from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...core.lib.colors import CHART
from ...core.lib.date import current_day
from ...core.lib.utils import get_value_from_dict as get_val
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...plans.lib.calc_day_sum import PlanCalculateDaySum
from ...savings.models import Saving
from ..lib.day_spending import DaySpending
from ..lib.expense_summary import ExpenseBase
from .common import expense_types


class MonthService():
    def __init__(self, request, year, month):
        self._request = request
        self._year = year
        self._month = month

        qs_expenses = Expense.objects.sum_by_day_ant_type(year, month)
        qs_savings = Saving.objects.sum_by_day(year, month)

        self.E = \
            ExpenseBase.days_of_month(
                year,
                month,
                qs_expenses,
                **{_('Savings'): qs_savings})

        self._day_plans = PlanCalculateDaySum(year)

        self._spending = DaySpending(
            year=year,
            month=month,
            expenses=qs_expenses,
            necessary=self._necessary_expense_types(_('Savings')),
            plan_day_sum=get_val(self._day_plans.day_input, month),
            plan_free_sum=get_val(self._day_plans.expenses_free, month),
        )

        self._expenses_types = expense_types(_('Savings'))

    def render_chart_targets(self):
        targets = self._day_plans.targets(self._month, _('Savings'))
        (categories, data_target, data_fact) = self._chart_targets(self._expenses_types, targets)

        context = {
            'chart_targets_categories': categories,
            'chart_targets_data_target': data_target,
            'chart_targets_data_fact': data_fact,
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_month_targets.html',
            context=context,
            request=self._request
        )

    def render_chart_expenses(self):
        context = {
            'expenses': self._chart_expenses(self._expenses_types)
        }

        return render_to_string(
            template_name='bookkeeping/includes/chart_month_expenses.html',
            context=context,
            request=self._request
        )

    def render_info(self):
        fact_incomes = Income.objects.sum_by_month(self._year, self._month)
        fact_incomes = float(fact_incomes[0]['sum']) if fact_incomes else 0.0
        fact_savings = self.E.total_row.get(_('Savings'))
        fact_savings = fact_savings if fact_savings else 0.0
        fact_expenses = self.E.total - fact_savings
        fact_per_day = self._spending.avg_per_day
        fact_balance = fact_incomes - fact_expenses - fact_savings

        plan_incomes = get_val(self._day_plans.incomes, self._month)
        plan_savings = get_val(self._day_plans.savings, self._month)
        plan_expenses = plan_incomes - plan_savings
        plan_per_day = get_val(self._day_plans.day_input, self._month)
        plan_balance = get_val(self._day_plans.remains, self._month)

        items = [{
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

        return render_to_string(
            template_name='bookkeeping/includes/spending_info.html',
            context={'items': items},
            request=self._request
        )

    def render_month_table(self):
        context = {
            'expenses': it.zip_longest(self.E.balance,
                                       self.E.total_column,
                                       self._spending.spending),
            'total': self.E.total,
            'total_row': self.E.total_row,
            'expense_types': self._expenses_types,
            'day': current_day(self._year, self._month, False),
        }

        return render_to_string(
            template_name='bookkeeping/includes/month_table.html',
            context=context,
            request=self._request
        )

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

    def _chart_expenses(self, expenses_types: List[str]) -> List[Dict]:
        rtn = []

        # make List[Dict] from expenses_types and total_row
        for name in expenses_types:
            value = self.E.total_row.get(name, 0.0)
            arr = {'name': name.upper(), 'y': value}
            rtn.append(arr)

        # sort List[Dict] by y
        rtn = sorted(rtn, key=itemgetter('y'), reverse=True)

        # add to List[Dict] colors
        for key, arr in enumerate(rtn):
            rtn[key]['color'] = CHART[key]

        return rtn

    def _chart_targets(self,
                      expenses_types: List[str],
                      targets: Dict
                      ) -> Tuple[List[str], List[float], List[Dict]]:
        tmp = []

        # make List[Dict] from expenses_types and total_row
        for name in expenses_types:
            value = self.E.total_row.get(name, 0.0)
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
