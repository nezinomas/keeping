from datetime import datetime

from django.db.models import F
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView

from ...core.forms import SearchForm
from ...core.lib import search
from ...core.mixins.ajax import AjaxCustomFormMixin
from ...core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                  DispatchAjaxMixin, IndexMixin, ListMixin,
                                  UpdateAjaxMixin)
from .. import forms, models
from ..apps import App_name
from ..views.expenses_type import Lists as TypeLists


def _qs_default_ordering(qs):
    return qs.order_by('-date', 'expense_type', F('expense_name').asc())


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': TypeLists.as_view()(self.request, as_string=True),
            'current_month': datetime.now().month,
            'search': render_to_string(
                template_name='core/includes/search_form.html',
                context={'form': SearchForm(), 'url': reverse('expenses:expenses_search')},
                request=self.request
            ),
            **context_to_reload(self.request)
        })

        return context


class MonthLists(IndexMixin):
    model = models.Expense

    def get_context_data(self, **kwargs):
        month = self.kwargs.get('month')

        context = super().get_context_data(**kwargs)
        context.update({
            'categories': TypeLists.as_view()(self.request, as_string=True),
            'current_month': month,
            **context_to_reload(self.request, month),
        })

        return context


class Lists(ListMixin):
    model = models.Expense

    def get_queryset(self):
        return _qs_default_ordering(super().get_queryset())


class New(CreateAjaxMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    list_render_output = False


class Update(UpdateAjaxMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    list_render_output = False


class Delete(DeleteAjaxMixin):
    model = models.Expense


class Search(AjaxCustomFormMixin):
    template_name = 'core/includes/search_form.html'
    form_class = SearchForm
    form_data_dict = {}
    url = reverse_lazy('expenses:expenses_search')

    def form_valid(self, form, **kwargs):
        _search = self.form_data_dict['search']

        sql = search.search_expenses(_search)
        if sql:
            template = 'expenses/includes/expenses_list.html'
            context = {'items': sql}
            kwargs.update({'html': render_to_string(template, context, self.request)})

        return super().form_valid(form, **kwargs)


class ReloadExpenses(DispatchAjaxMixin, TemplateView):
    template_name = f'{App_name}/includes/reload_expenses.html'
    redirect_view = f'{App_name}:{App_name}_index'

    def get(self, request, *args, **kwargs):
        month = request.GET.get('month')

        context = context_to_reload(request, month)

        return self.render_to_response(context=context)


def load_expense_name(request):
    pk = request.GET.get('expense_type')
    objects = models.ExpenseName.objects.parent(pk).year(request.user.year)

    return render(
        request,
        'core/dropdown.html',
        {'objects': objects}
    )


def context_to_reload(request, month=None):
    year = request.user.year
    month = int(month) if month else datetime.now().month

    qs = models.Expense.objects.year(year)

    if month in range(1, 13):
        qs = qs.filter(date__month=month)

    qs = _qs_default_ordering(qs)

    data = {
        'expenses_list': render_to_string(
            'expenses/includes/expenses_list.html', {
                'items': qs,
                'notice': f'{month} mėnesį įrašų nėra.',
            },
            request)
    }
    return data
