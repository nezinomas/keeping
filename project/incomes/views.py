from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..core.forms import SearchForm
from ..core.lib import search
from ..core.mixins.ajax import AjaxSearchMixin
from ..core.mixins.views import (CreateAjaxMixin, DeleteAjaxMixin,
                                 DispatchListsMixin, IndexMixin, ListMixin,
                                 UpdateAjaxMixin)
from . import forms, models


class Index(IndexMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'incomes': Lists.as_view()(self.request, as_string=True),
            'categories': TypeLists.as_view()(self.request, as_string=True),
            'search': Search.as_view()(self.request, as_string=True)
        })

        return context


#----------------------------------------------------------------------------------------
#                                                                                  Income
#----------------------------------------------------------------------------------------
class GetQuerySetMixin():
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .order_by('-date', 'price')
        )


class Lists(DispatchListsMixin, GetQuerySetMixin, ListMixin):
    model = models.Income


class New(GetQuerySetMixin, CreateAjaxMixin):
    model = models.Income
    form_class = forms.IncomeForm


class Update(GetQuerySetMixin, UpdateAjaxMixin):
    model = models.Income
    form_class = forms.IncomeForm


class Delete(DeleteAjaxMixin):
    model = models.Income


#----------------------------------------------------------------------------------------
#                                                                             Income Type
#----------------------------------------------------------------------------------------
class TypeLists(DispatchListsMixin, ListMixin):
    model = models.IncomeType


class TypeNew(CreateAjaxMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm


class TypeUpdate(UpdateAjaxMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm


#----------------------------------------------------------------------------------------
#                                                                                 Search
#----------------------------------------------------------------------------------------
class Search(AjaxSearchMixin):
    template_name = 'core/includes/search_form.html'
    form_class = SearchForm
    form_data_dict = {}
    url = reverse_lazy('incomes:incomes_search')
    update_container = 'ajax-content'

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_form(self.get_context_data())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        _search = self.form_data_dict['search']
        context = {'items': None}
        sql = search.search_incomes(_search)

        if sql:
            context = {'items': sql}
        else:
            context['notice'] = _('Found nothing')

        template = 'incomes/includes/incomes_list.html'
        kwargs.update({'html': render_to_string(template, context, self.request)})

        return super().form_valid(form, **kwargs)
