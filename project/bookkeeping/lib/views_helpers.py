from collections import Counter, defaultdict
from datetime import datetime
from typing import List

from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from ...core.lib.utils import sum_col
from ...expenses.models import Expense, ExpenseType
from ...incomes.models import Income
from ...savings.models import Saving
from ..lib.expense_summary import MonthExpense


def expense_types(*args: str) -> List[str]:
    qs = (
        ExpenseType
        .objects
        .items()
        .values_list('title', flat=True)
    )

    arr = []
    [arr.append(x) for x in qs]
    [arr.append(x) for x in args]

    arr.sort()

    return arr


def necessary_expense_types(*args: str) -> List[str]:
    qs = list(
        ExpenseType
        .objects
        .items()
        .filter(necessary=True)
        .values_list('title', flat=True)
    )

    list(qs.append(x) for x in args)

    qs.sort()

    return qs


def average(qs):
    now = datetime.now()
    arr = []

    for r in qs:
        year = r['year']
        sum_val = float(r['sum'])

        cnt = now.month if year == now.year else 12

        arr.append(sum_val / cnt)

    return arr


def add_latest_check_key(model, arr, year):
    items = model.objects.items(year)

    if items:
        for a in arr:
            latest = [x['latest_check'] for x in items if x.get('title') == a['title']]
            a['latest_check'] = latest[0] if latest else None


class ExpensesHelper():
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


class DetailedHelper():
    def __init__(self, year, *args, **kwargs):
        self._year = year

    def incomes_context(self, context):
        qs = Income.objects.sum_by_month_and_type(self._year)

        if not qs:
            return context

        return self._detailed_context(context, qs, _('Incomes'))

    def savings_context(self, context):
        qs = Saving.objects.sum_by_month_and_type(self._year)

        if not qs:
            return context

        return self._detailed_context(context, qs, _('Savings'))

    def expenses_context(self, context):
        qs = Expense.objects.sum_by_month_and_name(self._year)
        expenses_types = expense_types()

        for title in expenses_types:
            filtered = [*filter(lambda x: title in x['type_title'], qs)]

            if not filtered:
                continue

            self._detailed_context(
                context=context,
                data=filtered,
                name=_('Expenses / %(title)s') % ({'title': title})
            )

        return context

    def _detailed_context(self, context, data, name):
        context = context if context else {}

        if 'data' not in context.keys():
            context['data'] = []

        total_row = self._sum_detailed(data, 'date', ['sum'])
        total_col = self._sum_detailed(data, 'title', ['sum'])
        total = sum_col(total_col, 'sum')

        context['data'].append({
            'name': name,
            'data': data,
            'total_row': total_row,
            'total_col': total_col,
            'total': total,
        })

        return context

    def _sum_detailed(self, dataset, group_by_key, sum_value_keys):
        container = defaultdict(Counter)

        for item in dataset:
            key = item[group_by_key]
            values = {k: item[k] for k in sum_value_keys}
            container[key].update(values)

        new_dataset = []
        for item in container.items():
            new_dataset.append({group_by_key: item[0], **item[1]})

        new_dataset.sort(key=lambda item: item[group_by_key])

        return new_dataset
