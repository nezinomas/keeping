from django.urls import reverse_lazy

from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, UpdateViewMixin)
from . import forms, models


class Lists(ListViewMixin):
    model = models.Pension

    def get_queryset(self):
        return models.Pension.objects.year(year=self.request.user.year)


class New(CreateViewMixin):
    model = models.Pension
    form_class = forms.PensionForm
    success_url = reverse_lazy('pensions:list')

    hx_trigger = 'afterPension'


class Update(UpdateViewMixin):
    model = models.Pension
    form_class = forms.PensionForm
    success_url = reverse_lazy('pensions:list')

    hx_trigger = 'afterPension'


class Delete(DeleteViewMixin):
    model = models.Pension
    success_url = reverse_lazy('pensions:list')

    hx_trigger = 'afterPension'


class TypeLists(ListViewMixin):
    model = models.PensionType


class TypeNew(CreateViewMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm
    success_url = reverse_lazy('pensions:type_list')

    url = reverse_lazy('pensions:type_new')
    hx_trigger = 'afterPensionType'


class TypeUpdate(UpdateViewMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm
    success_url = reverse_lazy('pensions:type_list')

    hx_trigger = 'afterPensionType'
