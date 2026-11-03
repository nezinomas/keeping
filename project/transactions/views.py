from functools import cached_property

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..accounts.services.model_services import AccountModelService
from ..core.lib.convert_price import PriceToFloatViewMixin
from ..core.lib.utils import int_or_zero
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    UpdateViewMixin,
)
from ..savings.services.model_services import SavingTypeModelService
from . import forms
from .services.account_scope import AccountScope
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
    def get_queryset(self):
        user = self.request.user
        return TransactionModelService(user).year(user.selected_year())


class TabSales(TabViewMixin, ListViewMixin):
    tab = TABS["sales"]

    def get_queryset(self):
        user = self.request.user
        return SavingCloseModelService(user).year(user.selected_year())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {**context, "moves": with_close_marks(context["object_list"])}


class TabSwitches(TabViewMixin, ListViewMixin):
    tab = TABS["switches"]

    def get_queryset(self):
        user = self.request.user
        return SavingChangeModelService(user).year(user.selected_year())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {**context, "moves": with_close_marks(context["object_list"])}


class TabAccounts(TabViewMixin, ListViewMixin):
    tab = TABS["accounts"]

    @cached_property
    def scope(self) -> AccountScope:
        return AccountScope.parse(self.kwargs["scope"])

    def get_queryset(self):
        user = self.request.user
        return self.scope.rows(AccountModelService(user), user.selected_year())

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "items": self.scope.items(),
            # the scope shown, so a save reloads it rather than the tab's open url
            "tab_url": self.scope.url(),
        }


class LoadSavingType(ListViewMixin):
    template_name = "core/dropdown.html"

    def get(self, request, *args, **kwargs):
        pk = int_or_zero(request.GET.get("from_account"))
        if not pk:
            return self.render_to_response({"object_list": []})

        items = SavingTypeModelService(request.user).items().exclude(pk=pk)
        return self.render_to_response({"object_list": items})


class New(CreateViewMixin):
    form_class = forms.TransactionForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("transactions:index")
    modal_form_title = _("Transaction")


class Update(PriceToFloatViewMixin, UpdateViewMixin):
    service_class = TransactionModelService
    form_class = forms.TransactionForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("transactions:index")
    modal_form_title = _("Transaction")


class Delete(DeleteViewMixin):
    service_class = TransactionModelService
    success_url = reverse_lazy("transactions:index")
    modal_form_title = _("Delete transaction")


class SavingsCloseNew(CreateViewMixin):
    form_class = forms.SavingCloseForm
    hx_trigger_django = "reload"
    url_name = "savings_close_new"

    success_url = reverse_lazy("transactions:tab_sales")
    modal_form_title = _("Fund ⇒ Account")


class SavingsCloseUpdate(PriceToFloatViewMixin, UpdateViewMixin):
    service_class = SavingCloseModelService
    form_class = forms.SavingCloseForm
    hx_trigger_django = "reload"
    url_name = "savings_close_update"

    success_url = reverse_lazy("transactions:tab_sales")
    modal_form_title = _("Fund ⇒ Account")


class SavingsCloseDelete(DeleteViewMixin):
    service_class = SavingCloseModelService
    url_name = "savings_close_delete"

    success_url = reverse_lazy("transactions:tab_sales")
    modal_form_title = _("Delete transaction")


class SavingsChangeNew(CreateViewMixin):
    form_class = forms.SavingChangeForm
    hx_trigger_django = "reload"
    url_name = "savings_change_new"

    success_url = reverse_lazy("transactions:tab_switches")
    modal_form_title = _("Fund ⇔ Fund")


class SavingsChangeUpdate(PriceToFloatViewMixin, UpdateViewMixin):
    service_class = SavingChangeModelService
    form_class = forms.SavingChangeForm
    hx_trigger_django = "reload"
    url_name = "savings_change_update"

    success_url = reverse_lazy("transactions:tab_switches")
    modal_form_title = _("Fund ⇔ Fund")


class SavingsChangeDelete(DeleteViewMixin):
    service_class = SavingChangeModelService
    url_name = "savings_change_delete"

    success_url = reverse_lazy("transactions:tab_switches")
    modal_form_title = _("Delete transaction")
