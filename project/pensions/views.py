from django.urls import reverse_lazy

from ..core.lib.convert_price import ConvertToCents
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    UpdateViewMixin,
)
from . import forms, models


class Lists(ListViewMixin):
    model = models.Pension

    def get_queryset(self):
        return models.Pension.objects.year(year=self.request.user.year)


class New(CreateViewMixin):
    model = models.Pension
    form_class = forms.PensionForm
    hx_trigger_form = "afterPension"
    success_url = reverse_lazy("pensions:list")


class Update(ConvertToCents, UpdateViewMixin):
    model = models.Pension
    form_class = forms.PensionForm
    hx_trigger_django = "afterPension"
    success_url = reverse_lazy("pensions:list")


class Delete(DeleteViewMixin):
    model = models.Pension
    hx_trigger_django = "afterPension"
    success_url = reverse_lazy("pensions:list")


class TypeLists(ListViewMixin):
    model = models.PensionType


class TypeNew(CreateViewMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm
    hx_trigger_django = "afterPensionType"

    url = reverse_lazy("pensions:type_new")
    success_url = reverse_lazy("pensions:type_list")


class TypeUpdate(UpdateViewMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm
    hx_trigger_django = "afterPensionType"
    success_url = reverse_lazy("pensions:type_list")
