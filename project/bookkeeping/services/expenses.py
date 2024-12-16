import itertools as it
from dataclasses import dataclass, field

from django.utils.translation import gettext_lazy as _

from ...expenses.models import Expense, ExpenseType
from ..lib.balance_base import BalanceBase
from ..lib.make_dataframe import MakeDataFrame


@dataclass
class ExpenseServiceData:
    year: int
    expense_types: list = field(init=False, default_factory=list)
    expenses: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.expense_types = list(
            ExpenseType.objects.items().values_list("title", flat=True)
        )

        self.expenses = list(Expense.objects.sum_by_month_and_type(self.year))


class ExpenseService:
    def __init__(self, data: BalanceBase):
        self._types = data.types
        self._total = data.total
        self._total_row = data.total_row
        self._total_column = data.total_column
        self._balance = data.balance
        self._average = data.average

    def chart_context(self):
        if not self._types:
            return [{"name": _("No expenses"), "y": 0}]

        if arr := self._total_row.copy():
            # sort dictionary
            arr = dict(sorted(arr.items(), key=lambda x: x[1], reverse=True))

            # transform arr for bar chart
            return [{"name": key[:11], "y": value} for key, value in arr.items()]

        return [{"name": name[:11], "y": 0} for name in self._types]

    def table_context(self):
        return {
            "categories": self._types,
            "data": it.zip_longest(self._balance, self._total_column),
            "total": self._total,
            "total_row": self._total_row,
            "avg": self._calc_total_avg(self._total_row),
            "avg_row": self._average,
        }

    def _calc_total_avg(self, data: dict) -> float:
        return sum(values) / 12 if (values := data.values()) else 0


def load_service(year):
    data = ExpenseServiceData(year)
    df = MakeDataFrame(year, data.expenses, data.expense_types)
    return ExpenseService(BalanceBase(df.data))
