from django.template.loader import render_to_string

from ...expenses.models import Expense
from ..lib.expense_summary import MonthExpense
from .common import expense_types


class ExpensesService():
    def __init__(self, request, year):
        self._request = request
        self._year = year

        self._make_month_expense_object(year)

    def _make_month_expense_object(self, year: int) -> None:
        qs_expenses = Expense.objects.sum_by_month_and_type(year)

        self._MonthExpense = MonthExpense(
            year=year,
            expenses=qs_expenses,
            expenses_types=expense_types())

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
        context = {
            'year': self._year,
            'data': self._MonthExpense.balance,
            'categories': self._MonthExpense.expense_types,
            'total_row': self._MonthExpense.total_row,
            'avg_row': self._MonthExpense.average,
        }
        return render_to_string(
            template_name='bookkeeping/includes/year_expenses.html',
            context=context,
            request=self._request
        )

    def _chart_data(self, total_row) -> List[Dict[str, float]]:
        rtn = []
        arr = total_row.copy()

        if arr:
            # delete total cell
            del arr['total']

        if arr:
            # sort dictionary
            arr = dict(sorted(arr.items(), key=lambda x: x[1], reverse=True))

            # transfort arr for pie chart
            rtn = [{'name': key[:11], 'y': value}
                   for key, value in arr.items()]

        else:
            if self._expenses_types:
                rtn = [{'name': name[:11], 'y': 0}
                       for name in self._expenses_types]
            else:
                rtn = [{'name': _('No expenses'), 'y': 0}]

        return rtn
