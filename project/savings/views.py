from django.urls import reverse_lazy

from ..core.mixins.views import (CreateViewMixin, DeleteViewMixin,
                                 ListViewMixin, TemplateViewMixin,
                                 UpdateViewMixin)
from . import forms, models


class Index(TemplateViewMixin):
    template_name = 'savings/index.html'


class Lists(ListViewMixin):
    model = models.Saving


class New(CreateViewMixin):
    model = models.Saving
    form_class = forms.SavingForm
    success_url = reverse_lazy('savings:list')


class Update(UpdateViewMixin):
    model = models.Saving
    form_class = forms.SavingForm
    success_url = reverse_lazy('savings:list')


class Delete(DeleteViewMixin):
    model = models.Saving
    success_url = reverse_lazy('savings:list')


class TypeLists(ListViewMixin):
    model = models.SavingType

    def get_queryset(self):
        return models.SavingType.objects.related()


class TypeNew(CreateViewMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm
    success_url = reverse_lazy('savings:type_list')

    url = reverse_lazy('savings:type_new')
    hx_trigger = 'afterType'


class TypeUpdate(UpdateViewMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm

    hx_trigger = 'afterType'
