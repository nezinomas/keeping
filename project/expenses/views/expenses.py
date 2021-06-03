from datetime import datetime

from django.db.models import F
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from ...core.forms import SearchForm
from ...core.lib import search
from ...core.mixins.ajax import AjaxCustomFormMixin
from ...core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                  DispatchAjaxMixin, ListMixin,
                                  UpdateAjaxMixin)
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
            'search': render_search_form(self.request),
            'expenses_list': Lists.as_view()(self.request, as_string=True, **{'month': month}),
        })
        return context


class Lists(ListMixin):
    model = models.Expense
    template_name = 'expenses/includes/expenses_list.html'

    def get_context_data(self, **kwargs):
        month = self.kwargs.get('month')

        context = super().get_context_data(**kwargs)
        context.update({
            'notice': f'<b>{month}</b> mėnesį įrašų nėra.',
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
            kwargs.update({
                'container': 'expenses_list',
                'html': render_to_string(template, context, self.request)
            })

        return super().form_valid(form, **kwargs)


class ReloadExpenses(DispatchAjaxMixin, TemplateView):
    template_name = f'{App_name}/includes/reload_expenses.html'
    redirect_view = f'{App_name}:{App_name}_index'

    def get(self, request, *args, **kwargs):
        month = request.GET.get('month')
        context = {
            'expenses_list': Lists.as_view()(self.request, as_string=True, **{'month': month}),
        }

        return self.render_to_response(context=context)


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


def render_search_form(request):
    return (
        render_to_string(
            template_name='core/includes/search_form.html',
            context={
                'form': SearchForm(),
                'url': reverse('expenses:expenses_search')},
            request=request
        )
    )
