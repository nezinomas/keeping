from datetime import datetime

from django.db.models import F
from django.shortcuts import render
from django.template.loader import render_to_string

from ...core.lib.date import year_month_list
from ...core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                  UpdateAjaxMixin)
from .. import forms, models
from ..views.expenses_type import Lists as TypeLists


def _qs_default_ordering(qs):
    return qs.order_by('-date', 'expense_type', F('expense_name').asc())


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = TypeLists.as_view()(self.request, as_string=True)
        context['expenses'] = MonthLists.as_view()(self.request, as_string=True)

        context['buttons'] = year_month_list()
        context['current_month'] = datetime.now().month

        return context


class Lists(ListMixin):
    model = models.Expense

    def get_queryset(self):
        return _qs_default_ordering(super().get_queryset())


class MonthLists(ListMixin):
    model = models.Expense

    def get_queryset(self):
        month = self.kwargs.get('month')

        if not month or month not in range(1, 13):
            month = datetime.now().month

        qs = super().get_queryset().filter(date__month=month)
        return _qs_default_ordering(qs)


class New(CreateAjaxMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    list_render_output = False


class Update(UpdateAjaxMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    list_render_output = False


def load_expense_name(request):
    pk = request.GET.get('expense_type')
    objects = models.ExpenseName.objects.parent(pk).year(request.user.year)

    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )


def reload(request):
    year = request.user.year
    ajax_trigger = request.GET.get('ajax_trigger')
    name = 'expenses/includes/reload.html'

    context = {}

    if ajax_trigger:
        try:
            month = int(request.GET.get('month'))
        except:
            month = datetime.now().month

        qs = models.Expense.objects.year(year)
        if month in range(1, 13):
            qs = qs.filter(date__month=month)

        qs = _qs_default_ordering(qs)

        context['expenses_list'] = render_to_string(
            'expenses/includes/expenses_list.html',
            {'items': qs},
            request
        )

        return render(request, name, context)
