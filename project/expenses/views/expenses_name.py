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
    success_url = reverse_lazy("expenses:type_list")

    url = reverse_lazy("expenses:name_new")
    hx_trigger_django = "afterName"
    modal_form_title = _("Expense name")


class Update(QuerySetMixin, UpdateViewMixin):
    model = models.ExpenseName
    form_class = forms.ExpenseNameForm
    success_url = reverse_lazy("expenses:type_list")
    hx_trigger_django = "afterName"
    modal_form_title = _("Expense name")
