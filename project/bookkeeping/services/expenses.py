import itertools as it
from typing import Dict, List

from django.utils.translation import gettext as _

from ...expenses.models import Expense
from ..lib.expense_balance import ExpenseBalance
from .common import expense_types


class ExpenseService():
    def __init__(self, year: int) -> None:
        self._year = year
        self._expense_types = expense_types()

        obj = self._make_month_expense_object(year)

        self._balance = obj.balance
        self._total_column = obj.total_column
        self._total = obj.total
        self._total_row = obj.total_row
        self._average = obj.average

    def _make_month_expense_object(self, year: int) -> ExpenseBalance:
        qs = Expense.objects.sum_by_month_and_type(year)

        return \
            ExpenseBalance.months_of_year(year, qs, self._expense_types)

    def chart_context(self):
        return {
            'data': self._chart_data()
        }

    def table_context(self):
        return {
            'year': self._year,
            'categories': self._expense_types,
            'data': it.zip_longest(self._balance, self._total_column),
            'total': self._total,
            'total_row': self._total_row,
            'avg': self._calc_total_avg(),
            'avg_row': self._average,
        }

    def _calc_total_avg(self) -> float:
        return \
            sum(values) / 12 if (values := self._total_row.values()) else 0

    def _chart_data(self) -> List[Dict[str, float]]:
        if not self._expense_types:
            return [{'name': _('No expenses'), 'y': 0}]

        if arr := self._total_row.copy():
            # sort dictionary
            arr = dict(sorted(arr.items(), key=lambda x: x[1], reverse=True))

            # transform arr for bar chart
            return \
                [{'name': key[:11], 'y': value} for key, value in arr.items()]

        return \
            [{'name': name[:11], 'y': 0} for name in self._expense_types]
