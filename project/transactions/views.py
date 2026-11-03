from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

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


class TabTransactions(TabViewMixin, ListViewMixin):
    def get_queryset(self):
        user = self.request.user
        return TransactionModelService(user).year(user.selected_year())


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


class SavingsCloseLists(ListViewMixin):
    template_name = "transactions/savingclose_list.html"

    def get_queryset(self):
        user = self.request.user
        return SavingCloseModelService(user).year(year=user.selected_year())


class SavingsCloseNew(CreateViewMixin):
    form_class = forms.SavingCloseForm
    hx_trigger_form = "afterClose"
    url_name = "savings_close_new"

    success_url = reverse_lazy("transactions:savings_close_list")
    modal_form_title = _("Fund ⇒ Account")


class SavingsCloseUpdate(PriceToFloatViewMixin, UpdateViewMixin):
    service_class = SavingCloseModelService
    form_class = forms.SavingCloseForm
    hx_trigger_django = "afterClose"
    url_name = "savings_close_update"

    success_url = reverse_lazy("transactions:savings_close_list")
    modal_form_title = _("Fund ⇒ Account")


class SavingsCloseDelete(DeleteViewMixin):
    service_class = SavingCloseModelService
    hx_trigger_django = "afterClose"
    url_name = "savings_close_delete"

    success_url = reverse_lazy("transactions:savings_close_list")
    modal_form_title = _("Delete transaction")


class SavingsChangeLists(ListViewMixin):
    template_name = "transactions/savingchange_list.html"

    def get_queryset(self):
        user = self.request.user
        return SavingChangeModelService(user).year(year=user.selected_year())


class SavingsChangeNew(CreateViewMixin):
    form_class = forms.SavingChangeForm
    hx_trigger_form = "afterChange"
    url_name = "savings_change_new"

    success_url = reverse_lazy("transactions:savings_change_list")
    modal_form_title = _("Fund ⇔ Fund")


class SavingsChangeUpdate(PriceToFloatViewMixin, UpdateViewMixin):
    service_class = SavingChangeModelService
    form_class = forms.SavingChangeForm
    hx_trigger_django = "afterChange"
    url_name = "savings_change_update"

    success_url = reverse_lazy("transactions:savings_change_list")
    modal_form_title = _("Fund ⇔ Fund")


class SavingsChangeDelete(DeleteViewMixin):
    service_class = SavingChangeModelService
    hx_trigger_django = "afterChange"
    url_name = "savings_change_delete"

    success_url = reverse_lazy("transactions:savings_change_list")
    modal_form_title = _("Delete transaction")
