from datetime import datetime

from django.db.models import F
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from ...core.forms import SearchForm
from ...core.lib import search
from ...core.mixins.ajax import AjaxSearchMixin
from ...core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                  DispatchAjaxMixin, DispatchListsMixin,
                                  ListMixin, UpdateAjaxMixin)
from .. import forms, models
from ..apps import App_name
from ..views.expenses_type import Lists as TypeLists


class Index(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            'expenses:expenses_month_list',
            kwargs={'month': datetime.now().month}
        )


class MonthLists(ListMixin):
    model = models.Expense
    template_name = 'expenses/index.html'

    def get_context_data(self, **kwargs):
        month = self.kwargs.get('month')

        context = super().get_context_data(**kwargs)
        context.update({
            'categories': TypeLists.as_view()(self.request, as_string=True),
            'current_month': month,
            'search': Search.as_view()(self.request, as_string=True),
            'expenses_list': Lists.as_view()(self.request, as_string=True, month=month),
        })
        return context

class Lists(DispatchListsMixin, ListMixin):
    model = models.Expense
    template_name = 'expenses/includes/expenses_list.html'

    def get_context_data(self, **kwargs):
        month = self.kwargs.get('month')

        notice = _('There are no records for month <b>%(month)s</b>.') % {'month': month}
        if month == '13' or not month:
            notice = _('No records in <b>%(year)s</b>.') % {'year': self.request.user.year}

        context = super().get_context_data(**kwargs)
        context.update({
            'notice': notice,
        })
        return context

    def get_queryset(self):
        qs = super().get_queryset()

        month = self.kwargs.get('month')
        month = int(month) if month else month

        if month in range(1, 13):
            qs = qs.filter(date__month=month)

        qs = qs.order_by('-date', 'expense_type', F('expense_name').asc())

        return qs


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
    list_render_output = False


class Search(AjaxSearchMixin):
    template_name = 'core/includes/search_form.html'
    form_class = SearchForm
    form_data_dict = {}
    url = reverse_lazy('expenses:expenses_search')
    update_container = 'expenses_list'

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_form(self.get_context_data())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        _search = self.form_data_dict['search']
        context = {'items': None}
        sql = search.search_expenses(_search)

        if sql:
            context['items'] = sql
        else:
            context['notice'] = _('Found nothing')

        template = 'expenses/includes/expenses_list.html'
        kwargs.update({
            'html': render_to_string(template, context, self.request),
        })

        return super().form_valid(form, **kwargs)


class ReloadExpenses(DispatchAjaxMixin, TemplateView):
    template_name = f'{App_name}/includes/reload_expenses.html'
    redirect_view = reverse_lazy(f'{App_name}:{App_name}_index')

    def get(self, request, *args, **kwargs):
        month = request.GET.get('month')
        context = {
            'expenses_list': Lists.as_view()(self.request, as_string=True, **{'month': month}),
        }

        return JsonResponse(context)


class LoadExpenseName(TemplateView):
    template_name = 'core/dropdown.html'

    def get(self, request, *args, **kwargs):
        objects = []
        pk = request.GET.get('expense_type')

        if pk:
            objects = (models.ExpenseName
                       .objects
                       .parent(pk)
                       .year(request.user.year))

        return self.render_to_response({'objects': objects})
