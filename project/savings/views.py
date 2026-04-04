from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import ConvertPriceMixin
from ..core.lib.utils import rendered_content
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from ..pensions import views as pension_views
from . import forms
from .services.model_services import SavingModelService, SavingTypeModelService


class Index(TemplateViewMixin):
    template_name = "savings/index.html"

    def get_context_data(self, **kwargs):
        context = {
            "saving": rendered_content(self.request, Lists),
            "saving_type": rendered_content(self.request, TypeLists),
            "pension": rendered_content(self.request, pension_views.Lists),
            "pension_type": rendered_content(self.request, pension_views.TypeLists),
        }

        return {**super().get_context_data(**kwargs), **context}


class Lists(ListViewMixin):
    template_name = "savings/saving_list.html"
    service_class = SavingModelService

    def get_queryset(self):
        user = self.request.user
        return SavingModelService(user).year(user.year)


class New(CreateViewMixin):
    service_class = SavingModelService
    form_class = forms.SavingForm
    hx_trigger_form = "reload"
    success_url = reverse_lazy("savings:list")
    modal_form_title = _("Savings")


class Update(ConvertPriceMixin, UpdateViewMixin):
    service_class = SavingModelService
    form_class = forms.SavingForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:list")
    modal_form_title = _("Savings")


class Delete(DeleteViewMixin):
    service_class = SavingModelService
    success_url = reverse_lazy("savings:list")
    modal_form_title = _("Delete saving")


class TypeLists(ListViewMixin):
    template_name = "savings/savingtype_list.html"
    service_class = SavingTypeModelService

    def get_queryset(self):
        return (
            SavingTypeModelService(self.request.user)
            .all()
            .order_by("closed", "type", "title")
        )


class TypeNew(CreateViewMixin):
    service_class = SavingTypeModelService
    form_class = forms.SavingTypeForm
    url_name = "type_new"
    hx_trigger_django = "afterType"
    modal_form_title = _("Fund")
    success_url = reverse_lazy("savings:type_list")


class TypeUpdate(UpdateViewMixin):
    service_class = SavingTypeModelService
    form_class = forms.SavingTypeForm
    url_name = "type_update"
    hx_trigger_django = "afterType"
    modal_form_title = _("Fund")
    success_url = reverse_lazy("savings:type_list")
