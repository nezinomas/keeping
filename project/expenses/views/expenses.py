from django.db.models import F
from django.shortcuts import render
from django.template.loader import render_to_string

from ...core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                  UpdateAjaxMixin)
from .. import forms, models
from ..views.expenses_type import Lists as TypeLists


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = TypeLists.as_view()(self.request, as_string=True)
        context['expenses'] = Lists.as_view()(self.request, as_string=True)

        return context


class Lists(ListMixin):
    model = models.Expense

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .order_by('-date', 'expense_type', F('expense_name').asc())
        )


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
        context['expenses_list'] = render_to_string(
            'expenses/includes/expenses_list.html',
            {'items': models.Expense.objects.year(year)},
            request
        )

        return render(request, name, context)
