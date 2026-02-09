from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import ConvertPriceMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    UpdateViewMixin,
)
from . import forms, models
from .services.model_services import PensionModelService


class Lists(ListViewMixin):
    model = models.Pension

    def get_queryset(self):
        user = self.request.user
        return PensionModelService(user).year(user.year)


class New(CreateViewMixin):
    model = models.Pension
    form_class = forms.PensionForm
    hx_trigger_form = "afterPension"
    success_url = reverse_lazy("pensions:list")
    modal_form_title = _("Pension")


class Update(ConvertPriceMixin, UpdateViewMixin):
    model = models.Pension
    form_class = forms.PensionForm
    hx_trigger_django = "afterPension"
    success_url = reverse_lazy("pensions:list")
    modal_form_title = _("Pension")


class Delete(DeleteViewMixin):
    model = models.Pension
    hx_trigger_django = "afterPension"
    success_url = reverse_lazy("pensions:list")
    modal_form_title = _("Delete pension")


class TypeLists(ListViewMixin):
    model = models.PensionType


class TypeNew(CreateViewMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm
    hx_trigger_django = "afterPensionType"
    modal_form_title = _("Pension")
    url_name = "type_new"
    success_url = reverse_lazy("pensions:type_list")


class TypeUpdate(UpdateViewMixin):
    model = models.PensionType
    form_class = forms.PensionTypeForm
    hx_trigger_django = "afterPensionType"
    modal_form_title = _("Pension")
    url_name = "type_update"
    success_url = reverse_lazy("pensions:type_list")
