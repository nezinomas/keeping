from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import PriceToFloatViewMixin
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    UpdateViewMixin,
)
from . import forms
from .models import OTHER_PARTY
from .services.model_services import DebtModelService, DebtReturnModelService
from .tabs import DEBT_TABS, RETURN_TABS, TABS


class AddDebtTypeMixin:
    def url(self):
        # the route's kwargs carry the debt type, and the pk where there is one
        return reverse_lazy(self.url_name, kwargs=self.kwargs)

    def get_form_kwargs(self, **kwargs):
        kwargs["debt_type"] = self.kwargs.get("debt_type")
        return super().get_form_kwargs(**kwargs)


class DebtMixin:
    def get_success_url(self):
        return DEBT_TABS[self.kwargs["debt_type"]].url


class DebtReturnMixin:
    def get_success_url(self):
        return RETURN_TABS[self.kwargs["debt_type"]].url


class TabViewMixin(CoreTabViewMixin):
    tabs = TABS
    default_tab = TABS["lend"]
    app_title = _("Debts")
    page_template = "debts/index.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "other_party": OTHER_PARTY[self.tab.debt_type],
            "debt_type": self.tab.debt_type,
        }


class TabDebts(TabViewMixin, ListViewMixin):
    def get_queryset(self):
        user = self.request.user
        return DebtModelService(user, self.tab.debt_type).year(user.selected_year())


class TabLend(TabDebts):
    tab = TABS["lend"]


class TabBorrow(TabDebts):
    tab = TABS["borrow"]


class TabReturns(TabViewMixin, ListViewMixin):
    def get_queryset(self):
        user = self.request.user
        service = DebtReturnModelService(user, self.tab.debt_type)
        return service.year(user.selected_year())


class TabLendReturns(TabReturns):
    tab = TABS["lend_returns"]


class TabBorrowReturns(TabReturns):
    tab = TABS["borrow_returns"]


class DebtNew(AddDebtTypeMixin, DebtMixin, CreateViewMixin):
    url_name = "debts:new"
    form_class = forms.DebtForm
    hx_trigger_django = "reload"
    modal_form_title = _("Debt")


class DebtUpdate(PriceToFloatViewMixin, AddDebtTypeMixin, DebtMixin, UpdateViewMixin):
    url_name = "debts:update"
    form_class = forms.DebtForm
    hx_trigger_django = "reload"
    modal_form_title = _("Debt")

    def get_queryset(self):
        return DebtModelService(self.request.user, self.kwargs["debt_type"]).objects


class DebtDelete(AddDebtTypeMixin, DebtMixin, DeleteViewMixin):
    url_name = "debts:delete"
    modal_form_title = _("Delete debt")

    def get_queryset(self):
        return DebtModelService(self.request.user, self.kwargs["debt_type"]).objects


class DebtReturnNew(AddDebtTypeMixin, DebtReturnMixin, CreateViewMixin):
    url_name = "debts:return_new"
    form_class = forms.DebtReturnForm
    hx_trigger_django = "reload"
    modal_form_title = _("Debt return")


class DebtReturnUpdate(
    PriceToFloatViewMixin, AddDebtTypeMixin, DebtReturnMixin, UpdateViewMixin
):
    url_name = "debts:return_update"
    form_class = forms.DebtReturnForm
    hx_trigger_django = "reload"
    modal_form_title = _("Debt return")

    def get_queryset(self):
        return DebtReturnModelService(
            self.request.user, self.kwargs["debt_type"]
        ).objects


class DebtReturnDelete(AddDebtTypeMixin, DebtReturnMixin, DeleteViewMixin):
    url_name = "debts:return_delete"
    modal_form_title = _("Delete debt return")

    def get_queryset(self):
        return DebtReturnModelService(
            self.request.user, self.kwargs["debt_type"]
        ).objects
