from django.urls import reverse_lazy

from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, SearchMixin, TemplateViewMixin,
                                 UpdateViewMixin, rendered_content)
from . import forms, models


class Index(TemplateViewMixin):
    template_name = 'incomes/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'income': rendered_content(self.request, Lists),
            'income_type': rendered_content(self.request, TypeLists),
        })
        return context


class Lists(ListViewMixin):
    model = models.Income

    def get_queryset(self):
        return (
            models.Income.objects
            .year(year=self.request.user.year)
            .order_by('-date', 'price')
        )


class New(CreateViewMixin):
    model = models.Income
    form_class = forms.IncomeForm
    success_url = reverse_lazy('incomes:list')


class Update(UpdateViewMixin):
    model = models.Income
    form_class = forms.IncomeForm
    success_url = reverse_lazy('incomes:list')


class Delete(DeleteViewMixin):
    model = models.Income
    success_url = reverse_lazy('incomes:list')


class TypeLists(ListViewMixin):
    model = models.IncomeType


class TypeNew(CreateViewMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm
    success_url = reverse_lazy('incomes:type_list')
    hx_trigger = 'afterType'
    url = reverse_lazy('incomes:type_new')


class TypeUpdate(UpdateViewMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm
    hx_trigger = 'afterType'
    success_url = reverse_lazy('incomes:type_list')


class Search(SearchMixin):
    template_name = 'incomes/income_list.html'
    per_page = 50
    search_method = 'search_incomes'
