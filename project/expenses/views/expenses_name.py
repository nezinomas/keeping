from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ...core.mixins.views import CreateViewMixin, UpdateViewMixin
from .. import forms, models
from ..services.model_services import ExpenseNameModelService


class QuerySetMixin:
    def get_queryset(self):
        return ExpenseNameModelService(self.request.user).items()


class New(QuerySetMixin, CreateViewMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm
    hx_trigger_django = "afterName"
    modal_form_title = _("Expense name")
    url_name = "name_new"
    success_url = reverse_lazy("expenses:type_list")


class Update(QuerySetMixin, UpdateViewMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm
    hx_trigger_django = "afterName"
    modal_form_title = _("Expense name")
    url_name = "name_update"
    success_url = reverse_lazy("expenses:type_list")
