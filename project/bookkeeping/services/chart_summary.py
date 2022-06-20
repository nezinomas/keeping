from typing import Dict

from ...expenses.models import Expense
from ...incomes.models import Income
from .views_helpers import average


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

    def context(self, context) -> Dict:
        context = context if context else {}

        # generate balance_categories
        _arr = self._incomes if self._incomes else self._expenses
        balance_years = [x['year'] for x in _arr]

        records = len(balance_years)
        context['records'] = records

        if not records or records < 1:
            return context

        context.update({
            'balance_categories': balance_years,
            'balance_income_data': [*map(lambda x: float(x['sum']), self._incomes)],
            'balance_income_avg': average(self._incomes),
            'balance_expense_data': [*map(lambda x: float(x['sum']), self._expenses)],
        })

        # data for salary summary
        salary = self._get_salary()
        salary_years = [x['year'] for x in salary]

        context.update({
            'salary_categories': salary_years,
            'salary_data_avg': average(salary),
        })

        return context
