from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ...core.mixins.views import CreateViewMixin, ListViewMixin, UpdateViewMixin
from .. import forms, models
from ..services.model_services import ExpenseTypeModelService


class Lists(ListViewMixin):
    service_class = ExpenseTypeModelService
    template_name = "expenses/expensetype_list.html"


class New(CreateViewMixin):
    service_class = ExpenseTypeModelService
    form_class = forms.ExpenseTypeForm
    hx_trigger_django = "afterType"
    modal_form_title = _("Expense type")
    url_name = "type_new"
    success_url = reverse_lazy("expenses:type_list")


class Update(UpdateViewMixin):
    service_class = ExpenseTypeModelService
    form_class = forms.ExpenseTypeForm
    hx_trigger_django = "afterType"
    modal_form_title = _("Expense type")
    url_name = "type_update"
    success_url = reverse_lazy("expenses:type_list")
