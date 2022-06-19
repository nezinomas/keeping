from django.template.loader import render_to_string
from ..lib.views_helpers import expense_types
from ...expenses.models import Expense
from ..lib.expense_summary import MonthExpense


class ExpensesService():
    def __init__(self, request, year):
        self._request = request
        self._year = year

        self._expense_types = expense_types()
        qs_expenses = Expense.objects.sum_by_month_and_type(year)

        self._MonthExpense = MonthExpense(
            year=year,
            expenses=qs_expenses,
            expenses_types=self._expense_types)

    def render_chart_expenses(self):
        context = {
            'data': self._MonthExpense.chart_data
        }
        return render_to_string(
            template_name='bookkeeping/includes/chart_expenses.html',
            context=context,
            request=self._request
        )

    def render_year_expenses(self):
        _expense_types = self._expense_types

        context = {
            'year': self._year,
            'data': self._MonthExpense.balance,
            'categories': _expense_types,
            'total_row': self._MonthExpense.total_row,
            'avg_row': self._MonthExpense.average,
        }
        return render_to_string(
            template_name='bookkeeping/includes/year_expenses.html',
            context=context,
            request=self._request
        )
