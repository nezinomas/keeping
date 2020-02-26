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

        return context


#
# Income views
#
class Lists(ListMixin):
    model = models.Income

    def get_queryset(self):
        return super().get_queryset().order_by('-date', 'price')


class New(CreateAjaxMixin):
    model = models.Income
    form_class = forms.IncomeForm


class Update(UpdateAjaxMixin):
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
