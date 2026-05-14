from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import ConvertPriceMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    SearchViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from . import forms
from .services.model_services import IncomeModelService, IncomeTypeModelService


class Index(TemplateViewMixin):
    template_name = "incomes/index.html"


class Lists(ListViewMixin):
    template_name = "incomes/income_list.html"
    service_class = IncomeModelService

    def get_queryset(self):
        user = self.request.user
        return IncomeModelService(user).year(user.year).order_by("-date", "price")


class New(CreateViewMixin):
    service_class = IncomeModelService
    form_class = forms.IncomeForm
    success_url = reverse_lazy("incomes:list")
    hx_trigger_form = "reload"
    modal_form_title = _("Incomes")


class Update(ConvertPriceMixin, UpdateViewMixin):
    service_class = IncomeModelService
    form_class = forms.IncomeForm
    success_url = reverse_lazy("incomes:list")
    hx_trigger_django = "reload"
    modal_form_title = _("Incomes")


class Delete(DeleteViewMixin):
    service_class = IncomeModelService
    success_url = reverse_lazy("incomes:list")
    modal_form_title = _("Delete income")


class TypeLists(ListViewMixin):
    template_name = "incomes/incometype_list.html"
    service_class = IncomeTypeModelService


class TypeNew(CreateViewMixin):
    service_class = IncomeTypeModelService
    form_class = forms.IncomeTypeForm
    hx_trigger_django = "afterType"
    modal_form_title = _("Incomes type")
    url_name = "type_new"
    success_url = reverse_lazy("incomes:type_list")


class TypeUpdate(UpdateViewMixin):
    service_class = IncomeTypeModelService
    form_class = forms.IncomeTypeForm
    hx_trigger_django = "afterType"
    modal_form_title = _("Incomes type")
    url_name = "type_update"
    success_url = reverse_lazy("incomes:type_list")


class Search(SearchViewMixin):
    template_name = "incomes/income_list.html"
    search_method = "search_incomes"
    per_page = 50
