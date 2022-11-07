from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from ...expenses.models import Expense
from ...incomes.models import Income
from . import common


@dataclass
class ChartSummaryServiceData:
    incomes: list = field(init=False, default_factory=list)
    expenses: list = field(init=False, default_factory=list)
    salary: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = \
            Income.objects \
            .sum_by_year()
        self.salary = \
            Income.objects \
            .sum_by_year() \
            .filter(income_type__type="salary")
        self.expenses = \
            Expense.objects.sum_by_year()


class ChartSummaryService:
    def __init__(self, data: ChartSummaryServiceData):
        self._incomes = data.incomes
        self._salary = data.salary
        self._expenses = data.expenses

    def chart_balance(self) -> dict:
        # generate balance_categories
        data = self._incomes or self._expenses
        balance_years = [x['year'] for x in data]

        records = len(balance_years)
        context = {'records': records}

        if not records or records < 1:
            return context

        context |= {
            'chart_title': _('Incomes/Expenses'),
            'categories': balance_years,
            'incomes': [*map(lambda x: float(x['sum']), self._incomes)],
            'incomes_title': _('Incomes'),
            'expenses': [*map(lambda x: float(x['sum']), self._expenses)],
            'expenses_title': _('Expenses'),
        }

        return context

    def chart_incomes(self) -> dict:
        # data for salary summary
        salary_years = [x['year'] for x in self._salary]

        records = len(salary_years)
        context = {'records': records}

        if not records or records < 1:
            return context

        context |= {
            'chart_title': _('Incomes'),
            'categories': salary_years,
            'incomes': common.average(self._incomes),
            'incomes_title': _('Average incomes'),
            'salary': common.average(self._salary),
            'salary_title': _('Average salary') + ', €',
        }

        return context
