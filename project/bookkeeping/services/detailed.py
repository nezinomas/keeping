from collections import Counter, defaultdict

from django.utils.translation import gettext as _

from ...core.lib.utils import sum_col
from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from .views_helpers import expense_types


class DetailedService():
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
