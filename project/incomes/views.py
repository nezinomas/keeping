from django.core.paginator import Paginator
from django.http import JsonResponse
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
    list_template = 'incomes/includes/list.html'
    form_class = SearchForm
    form_data_dict = {}
    url = reverse_lazy('incomes:search')
    per_page = 50

    def dispatch(self, request, *args, **kwargs):
        if 'as_string' in kwargs:
            return self._render_form(self.get_context_data())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        search_str = self.form_data_dict['search']
        sql = search.search_incomes(search_str)
        paginator = Paginator(sql, self.per_page)
        page_range = paginator.get_elided_page_range(number=1)

        if sql:
            context = {
                'items': paginator.get_page(1),
                'search': search_str,
                'page_range': page_range,
                'url': self.url,
            }
        else:
            context = {
                'items': None,
                'notice': _('Found nothing'),
            }

        kwargs.update({
            'html': render_to_string(self.list_template, context, self.request),
        })

        return super().form_valid(form, **kwargs)

    def get(self, request, *args, **kwargs):
        _page = request.GET.get('page')
        _search = request.GET.get('search')

        if _page and _search:
            sql = search.search_incomes(_search)
            paginator = Paginator(sql, self.per_page)
            page_range = paginator.get_elided_page_range(number=_page)

            context = {
                'items': paginator.get_page(_page),
                'search': _search,
                'page_range': page_range,
                'url': self.url,
            }

            _page = render_to_string(self.list_template, context, self.request)

            return JsonResponse({'xxx': _page})

        return super().get(request, *args, **kwargs)
