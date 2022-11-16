import itertools
import operator
from dataclasses import dataclass, field


from django.utils.translation import gettext as _

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
        self.incomes = Income.objects.sum_by_month_and_type(self.year)
        self.savings = Saving.objects.sum_by_month_and_type(self.year)
        self.expenses = Expense.objects.sum_by_month_and_name(self.year)
        self.expenses_types = list(
            ExpenseType.objects
            .items()
            .values_list('title', flat=True)
        )


class DetailedService():
    def __init__(self, data: DetailerServiceData):
        self._incomes = data.incomes
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

        items = dict(name=name, items=[], total_row=[0.0] * 13)

        # sort data by title and date
        data = sorted(data, key=operator.itemgetter("title", 'date'))

        # group data by title and calculate totals
        for title, group in itertools.groupby(data, key=operator.itemgetter("title")):
            items['items'].append({'title': title, 'data': [0.0] * 13})

            for i, r in enumerate(group):
                sum_ = float(r['sum'])

                # last array
                item = items['items'][-1]
                item['data'][i] = sum_
                item['data'][12] += sum_  # total column

                items['total_row'][i] += sum_
                items['total_row'][12] += sum_  # total column

        return items
