from django.http import JsonResponse
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.ajax import AjaxCustomFormMixin
from ..core.mixins.views import (CreateAjaxMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['incomes'] = Lists.as_view()(
            self.request, as_string=True)
        context['categories'] = TypeLists.as_view()(
            self.request, as_string=True)
        context['search'] = render_to_string(
            template_name='core/includes/search_form.html',
            context={'form': SearchForm(), 'url': reverse('incomes:incomes_search')},
            request=self.request
        )

        return context


#
# Income views
#
class GetQuerySetMixin():
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .order_by('-date', 'price')
        )


class Lists(GetQuerySetMixin, ListMixin):
    model = models.Income


class New(GetQuerySetMixin, CreateAjaxMixin):
    model = models.Income
    form_class = forms.IncomeForm


class Update(GetQuerySetMixin, UpdateAjaxMixin):
    model = models.Income
    form_class = forms.IncomeForm


#
# IncomeType views
#
class TypeLists(ListMixin):
    model = models.IncomeType


class TypeNew(CreateAjaxMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm


class Search(AjaxCustomFormMixin):
    template_name = 'core/includes/search_form.html'
    form_class = SearchForm
    form_data_dict = {}
    url = reverse_lazy('incomes:incomes_search')

    def form_valid(self, form):
        html = 'Nieko neradau'
        _search = self.form_data_dict['search']

        sql = search.search_incomes(_search)
        if sql:
            template = 'incomes/includes/incomes_list.html'
            context = {'items': sql}
            html = render_to_string(template, context, self.request)

        data = {
            'form_is_valid': True,
            'html_form': self._render_form({'form': form}),
            'html': html,
        }
        return JsonResponse(data)
