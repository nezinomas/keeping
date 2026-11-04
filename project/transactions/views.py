from functools import cached_property

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import PriceToFloatViewMixin
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    LoadToAccountViewMixin,
    UpdateViewMixin,
)
from ..savings.services.model_services import SavingTypeModelService
from . import forms
from .services.close_year import FundCloseYear
from .services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)
from .tabs import TABS


class TabViewMixin(CoreTabViewMixin):
    tabs = TABS
    default_tab = TABS["transactions"]
    app_title = _("Transactions")
    page_template = "transactions/index.html"


def with_close_marks(moves) -> list[tuple]:
    """Each Fund sale or switch beside whether it closed its Fund, one read for all."""
    moves = list(moves)
    funds = FundCloseYear.of_funds({move.from_account_id for move in moves})
    return [(move, funds[move.from_account_id].closes(move.date)) for move in moves]


class TabTransactions(TabViewMixin, ListViewMixin):
    tab = TABS["transactions"]

    def get_queryset(self):
        user = self.request.user
        return TransactionModelService(user).year(user.selected_year())


class TabFundMoves(TabViewMixin, ListViewMixin):
    """A tab of the year's Fund sales or switches, each beside its Close mark."""

    def get_queryset(self):
        user = self.request.user
        return self.service_class(user).year(user.selected_year())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {**context, "moves": with_close_marks(context["object_list"])}


class TabSales(TabFundMoves):
    tab = TABS["sales"]
    service_class = SavingCloseModelService


class TabSwitches(TabFundMoves):
    tab = TABS["switches"]
    service_class = SavingChangeModelService


class TabAccounts(TabViewMixin, ListViewMixin):
    tab = TABS["accounts"]

    @cached_property
    def service(self) -> AccountModelService:
        return AccountModelService(self.request.user)

    @cached_property
    def year(self) -> int:
        return self.request.user.selected_year()

    def get_queryset(self):
        return self.service.items_in(self.year)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "closed_accounts": self.service.closed_before(self.year),
        }


class LoadSavingType(LoadToAccountViewMixin):
    service_class = SavingTypeModelService


class TransactionsMixin:
    form_class = forms.TransactionForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("transactions:index")
    modal_form_title = _("Transaction")


class New(TransactionsMixin, CreateViewMixin):
    pass


class Update(TransactionsMixin, PriceToFloatViewMixin, UpdateViewMixin):
    service_class = TransactionModelService


class Delete(TransactionsMixin, DeleteViewMixin):
    service_class = TransactionModelService
    modal_form_title = _("Delete transaction")


class SalesMixin:
    form_class = forms.SavingCloseForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("transactions:tab_sales")
    modal_form_title = _("Fund ⇒ Account")


class SavingsCloseNew(SalesMixin, CreateViewMixin):
    url_name = "savings_close_new"


class SavingsCloseUpdate(SalesMixin, PriceToFloatViewMixin, UpdateViewMixin):
    service_class = SavingCloseModelService
    url_name = "savings_close_update"


class SavingsCloseDelete(SalesMixin, DeleteViewMixin):
    service_class = SavingCloseModelService
    url_name = "savings_close_delete"
    modal_form_title = _("Delete transaction")


class SwitchesMixin:
    form_class = forms.SavingChangeForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("transactions:tab_switches")
    modal_form_title = _("Fund ⇔ Fund")


class SavingsChangeNew(SwitchesMixin, CreateViewMixin):
    url_name = "savings_change_new"


class SavingsChangeUpdate(SwitchesMixin, PriceToFloatViewMixin, UpdateViewMixin):
    service_class = SavingChangeModelService
    url_name = "savings_change_update"


class SavingsChangeDelete(SwitchesMixin, DeleteViewMixin):
    service_class = SavingChangeModelService
    url_name = "savings_change_delete"
    modal_form_title = _("Delete transaction")
