from typing import Dict, List

from django.db.models.query import QuerySet
from django.utils.translation import gettext as _

from ...expenses.models import Expense
from ..lib.expense_summary import ExpenseBase
from .common import expense_types


class ExpenseService():
    def __init__(self, year: int) -> None:
        obj = self._make_month_expense_object(year)

        self._year = year
        self._balance = obj.balance
        self._total_row = obj.total_row
        self._average = obj.average

    def _make_month_expense_object(self, year: int) -> ExpenseBase:
        qs = Expense.objects.sum_by_month_and_type(year)

        self._expense_types = self._get_types(qs)

        return \
            ExpenseBase.months_of_year(year, qs, self._expense_types)

    def _get_types(self, qs: QuerySet) -> List:
        if qs.exists():
            # filter unique expense types
            types = []
            for row in qs:
                for key, value in row.items():
                    if key == 'title' and value not in types:
                        types.append(value)

            # sort expense types
            types.sort()

            return types

        # if no expenses get types from db
        return expense_types()

    def chart_expenses_context(self):
        return {
            'data': self._chart_data()
        }

    def year_expenses_context(self):
        return {
            'year': self._year,
            'data': self._balance,
            'categories': self._expense_types,
            'total_row': self._total_row,
            'avg_row': self._average,
        }

    def _chart_data(self) -> List[Dict[str, float]]:
        if not self._expense_types:
            return [{'name': _('No expenses'), 'y': 0}]

        arr = self._total_row.copy()

        if arr:
            # sort dictionary
            arr = dict(sorted(arr.items(), key=lambda x: x[1], reverse=True))

            # transform arr for bar chart
            return \
                [{'name': key[:11], 'y': value} for key, value in arr.items()]

        return \
            [{'name': name[:11], 'y': 0} for name in self._expense_types]
