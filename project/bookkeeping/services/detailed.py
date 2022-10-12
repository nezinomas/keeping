from collections import Counter, defaultdict

from django.utils.translation import gettext as _

from ...core.lib.utils import sum_col
from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from .common import expense_types


class DetailedService():
    def __init__(self, year, *args, **kwargs):
        self._year = year

    def incomes_context(self, context):
        return self._get_context(Income, _('Incomes'), context)

    def savings_context(self, context):
        return self._get_context(Saving, _('Savings'), context)

    def expenses_context(self, context):
        qs = Expense.objects.sum_by_month_and_name(self._year)
        expenses_types = expense_types()

        for title in expenses_types:
            if filtered := [*filter(lambda x: title in x['type_title'], qs)]:
                self._detailed_context(
                    context=context,
                    data=filtered,
                    name=_('Expenses / %(title)s') % ({'title': title})
                )
        return context

    def _get_context(self, model, title, context):
        qs = \
            model.objects \
            .sum_by_month_and_type(self._year)

        updated_context = self._detailed_context(context, qs, title)
        return updated_context if qs else context

    def _detailed_context(self, context, data, name):
        context = context or {}

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

        new_dataset = [{group_by_key: item[0], **item[1]} for item in container.items()]

        new_dataset.sort(key=lambda item: item[group_by_key])

        return new_dataset
