from collections import Counter, defaultdict
from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from ...core.lib.utils import sum_col
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...savings.models import Saving


@dataclass
class DetailerServiceData:
    year: int
    incomes: list[dict] = field(init=False, default_factory=list)
    expenses: list[dict] = field(init=False, default_factory=list)
    savings: list[dict] = field(init=False, default_factory=list)
    expenses_types: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.icomes = Income.objects.sum_by_month_and_type(self.year)
        self.savings = Saving.objects.sum_by_month_and_type(self.year)
        self.expenses = Expense.objects.sum_by_month_and_name(self.year)
        self.expenses_types = list(
            ExpenseType.objects
            .items()
            .values_list('title', flat=True)
        )


class DetailedService():
    def __init__(self, data: DetailerServiceData):
        self._year = data.year
        self._incomes = data.icomes
        self._expenses = data.expenses
        self._savings = data.savings
        self._expenses_types = data.expenses_types

    def incomes_context(self) -> list[dict]:
        return [self._context(_('Incomes'), self._incomes)]

    def savings_context(self) -> list[dict]:
        return [self._context(_('Savings'), self._savings)]

    def expenses_context(self) -> list[dict]:
        context = []
        for title in self._expenses_types:
            if filtered := [*filter(lambda x: title in x['type_title'], self._expenses)]:
                context.append(
                    self._context(
                        name=_('Expenses / %(title)s') % ({'title': title}),
                        data=filtered))
        return context

    def _context(self, name, data) -> dict:
        if not data:
            return {}

        total_row = self._sum_detailed(data, 'date', ['sum'])
        total_col = self._sum_detailed(data, 'title', ['sum'])
        total = sum_col(total_col, 'sum')

        return  {
            'name': name,
            'data': data,
            'total_row': total_row,
            'total_col': total_col,
            'total': total,
        }

    def _sum_detailed(self, dataset, group_by_key, sum_value_keys):
        container = defaultdict(Counter)

        for item in dataset:
            key = item[group_by_key]
            values = {k: item[k] for k in sum_value_keys}
            container[key].update(values)

        new_dataset = [{group_by_key: item[0], **item[1]} for item in container.items()]

        new_dataset.sort(key=lambda item: item[group_by_key])

        return new_dataset
