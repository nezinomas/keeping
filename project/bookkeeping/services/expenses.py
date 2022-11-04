import itertools as it
from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from ...expenses.models import Expense, ExpenseType
from ..lib.expense_balance import ExpenseBalance


@dataclass
class ExpenseServiceData:
    year: int

    expense_types: list = field(init=False, default_factory=list)
    expenses: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.expense_types = list(
            ExpenseType.objects \
            .items() \
            .values_list('title', flat=True)
        )

        self.expenses = \
            Expense.objects \
            .sum_by_month_and_type(self.year)


class ExpenseService():
    def __init__(self, data: ExpenseBalance):
        self._data = data

    def chart_context(self):
        if not self._data.types:
            return [{'name': _('No expenses'), 'y': 0}]

        if arr := self._data.total_row.copy():
            # sort dictionary
            arr = dict(sorted(arr.items(), key=lambda x: x[1], reverse=True))

            # transform arr for bar chart
            return \
                [{'name': key[:11], 'y': value} for key, value in arr.items()]

        return \
            [{'name': name[:11], 'y': 0} for name in self._data.types]


    def table_context(self):
        return {
            'categories': self._data.types,
            'data': it.zip_longest(self._data.balance, self._data.total_column),
            'total': self._data.total,
            'total_row': self._data.total_row,
            'avg': self._calc_total_avg(),
            'avg_row': self._data.average,
        }

    def _calc_total_avg(self) -> float:
        return \
            sum(values) / 12 if (values := self._data.total_row.values()) else 0
