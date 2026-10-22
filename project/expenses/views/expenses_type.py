from datetime import date

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ...core.lib.year_boundary import YearBoundary
from ...core.mixins.tabs import sorted_tab_urls
from ...core.mixins.views import CreateViewMixin, TemplateViewMixin, UpdateViewMixin
from .. import forms
from ..services.model_services import ExpenseTypeModelService
from ..services.type_rows import GroupedTypesTable
from ..tabs import TABS
from .expenses import TabViewMixin


class TabTypes(TabViewMixin, TemplateViewMixin):
    tab = TABS["types"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        table = GroupedTypesTable.read(
            user,
            YearBoundary(user.selected_year(), date.today()),
            self.request.GET.get("order", ""),
        )

        return {
            **super().get_context_data(**kwargs),
            "table": table,
            **sorted_tab_urls(self.tab, table.order),
        }


class New(CreateViewMixin):
    form_class = forms.ExpenseTypeForm
    hx_trigger_django = "reload"
    modal_form_title = _("Expense type")
    url_name = "type_new"
    success_url = reverse_lazy("expenses:tab_types")


class Update(UpdateViewMixin):
    service_class = ExpenseTypeModelService
    form_class = forms.ExpenseTypeForm
    hx_trigger_django = "reload"
    modal_form_title = _("Expense type")
    url_name = "type_update"
    success_url = reverse_lazy("expenses:tab_types")
