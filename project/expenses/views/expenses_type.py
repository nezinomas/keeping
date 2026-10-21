from datetime import date

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ...core.lib.year_boundary import YearBoundary
from ...core.mixins.tabs import sorted_tab_urls
from ...core.mixins.views import CreateViewMixin, TemplateViewMixin, UpdateViewMixin
from .. import forms
from ..services.model_services import (
    ExpenseModelService,
    ExpenseNameModelService,
    ExpenseTypeModelService,
)
from ..services.type_rows import GroupedTypesTable
from ..tabs import TABS
from .expenses import TabViewMixin


class TabTypes(TabViewMixin, TemplateViewMixin):
    tab = TABS["types"]

    def get_context_data(self, **kwargs):
        user = self.request.user
        boundary = YearBoundary(user.selected_year(), date.today())
        service = ExpenseModelService(user)
        types = ExpenseTypeModelService(user).items().values("id", "title", "necessary")
        names = (
            ExpenseNameModelService(user)
            .items()
            .values("id", "title", "parent_id", "valid_for")
        )

        table = GroupedTypesTable.build(
            types=list(types),
            names=list(names),
            year=list(service.sum_by_between("expense_name", *boundary.span)),
            last_year=list(
                service.sum_by_between("expense_name", *boundary.previous_span)
            ),
            last_dates=list(service.last_date_by("expense_name", boundary.end_date)),
            order=self.request.GET.get("order", ""),
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
