from typing import Dict

from django.utils.translation import gettext as _

from ...expenses.models import Expense
from ...incomes.models import Income
from .common import average


class ChartSummaryService:
    def __init__(self):
        self._incomes = self._get_incomes()
        self._expenses = self._get_expenses()

    def _get_incomes(self) -> Dict:
        return \
            Income.objects.sum_by_year()

    def _get_expenses(self) -> Dict:
        return \
            Expense.objects.sum_by_year()

    def _get_salary(self) -> Dict:
        return \
            self._incomes.filter(income_type__type="salary")

    def chart_balance(self) -> Dict:
        # generate balance_categories
        _arr = self._incomes or self._expenses
        balance_years = [x['year'] for x in _arr]

        records = len(balance_years)
        context = {'records': records}
        if not records or records < 1:
            return context

        context |= {
            'categories': balance_years,
            'incomes': [*map(lambda x: float(x['sum']), self._incomes)],
            'incomes_title': _('Incomes'),
            'expenses': [*map(lambda x: float(x['sum']), self._expenses)],
            'expenses_title': _('Expenses'),
            'chart_title': _('Incomes/Expenses'),
        }

        return context

    def chart_incomes(self, context) -> Dict:
        context = context or {}

        # data for salary summary
        salary = self._get_salary()
        salary_years = [x['year'] for x in salary]

        records = len(salary_years)
        context['records'] = records

        if not records or records < 1:
            return context

        context |= {
            'categories': salary_years,
            'chart_title': _('Incomes/Expenses'),
            'incomes': average(self._incomes),
            'salary': average(salary),
        }

        return context
