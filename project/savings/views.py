from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import ConvertToPriceMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
    rendered_content,
)
from ..pensions import views as pension_views
from . import forms, models
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
    model = models.Saving

    def get_queryset(self):
        user = self.request.user
        return SavingModelService(user).year(user.year)


class New(CreateViewMixin):
    model = models.Saving
    form_class = forms.SavingForm
    hx_trigger_form = "reload"
    success_url = reverse_lazy("savings:list")
    modal_form_title = _("Savings")


class Update(ConvertToPriceMixin, UpdateViewMixin):
    model = models.Saving
    form_class = forms.SavingForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:list")
    modal_form_title = _("Savings")


class Delete(DeleteViewMixin):
    model = models.Saving
    success_url = reverse_lazy("savings:list")
    modal_form_title = _("Delete saving")


class TypeLists(ListViewMixin):
    model = models.SavingType

    def get_queryset(self):
        return (
            SavingTypeModelService(self.request.user)
            .all()
            .order_by("closed", "type", "title")
        )


class TypeNew(CreateViewMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm
    url_name = "type_new"
    hx_trigger_django = "afterType"
    modal_form_title = _("Fund")
    success_url = reverse_lazy("savings:type_list")


class TypeUpdate(UpdateViewMixin):
    model = models.SavingType
    form_class = forms.SavingTypeForm
    url_name = "type_update"
    hx_trigger_django = "afterType"
    modal_form_title = _("Fund")
    success_url = reverse_lazy("savings:type_list")
