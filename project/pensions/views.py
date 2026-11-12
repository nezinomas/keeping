from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import PriceToFloatViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    UpdateViewMixin,
)
from . import forms
from .services.model_services import PensionModelService, PensionTypeModelService


class New(CreateViewMixin):
    form_class = forms.PensionForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:tab_pensions")
    modal_form_title = _("Pension")


class Update(PriceToFloatViewMixin, UpdateViewMixin):
    service_class = PensionModelService
    form_class = forms.PensionForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:tab_pensions")
    modal_form_title = _("Pension")


class Delete(DeleteViewMixin):
    service_class = PensionModelService
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:tab_pensions")
    modal_form_title = _("Delete pension")


class TypeNew(CreateViewMixin):
    form_class = forms.PensionTypeForm
    hx_trigger_django = "reload"
    modal_form_title = _("II stage fund")
    url_name = "type_new"
    success_url = reverse_lazy("savings:tab_pension_funds")


class TypeUpdate(UpdateViewMixin):
    service_class = PensionTypeModelService
    form_class = forms.PensionTypeForm
    hx_trigger_django = "reload"
    modal_form_title = _("II stage fund")
    url_name = "type_update"
    success_url = reverse_lazy("savings:tab_pension_funds")
