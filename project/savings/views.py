from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import PriceToFloatViewMixin
from ..core.mixins.tabs import ClosedFoldTabMixin
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    UpdateViewMixin,
)
from ..pensions.services.model_services import (
    PensionModelService,
    PensionTypeModelService,
)
from . import forms
from .services.model_services import SavingModelService, SavingTypeModelService
from .tabs import TABS


class TabViewMixin(CoreTabViewMixin):
    tabs = TABS
    default_tab = TABS["savings"]
    app_title = _("Savings")
    page_template = "savings/index.html"


class TabSavings(TabViewMixin, ListViewMixin):
    tab = TABS["savings"]

    def get_queryset(self):
        user = self.request.user
        return SavingModelService(user).year(user.selected_year())


class New(CreateViewMixin):
    form_class = forms.SavingForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:index")
    modal_form_title = _("Savings")


class Update(PriceToFloatViewMixin, UpdateViewMixin):
    service_class = SavingModelService
    form_class = forms.SavingForm
    hx_trigger_django = "reload"
    success_url = reverse_lazy("savings:index")
    modal_form_title = _("Savings")


class Delete(DeleteViewMixin):
    service_class = SavingModelService
    success_url = reverse_lazy("savings:index")
    modal_form_title = _("Delete saving")


class TabFunds(TabViewMixin, ClosedFoldTabMixin, ListViewMixin):
    tab = TABS["funds"]
    service_class = SavingTypeModelService
    closed_key = "closed_funds"
    order = SavingTypeModelService.ORDER


class TypeNew(CreateViewMixin):
    form_class = forms.SavingTypeForm
    url_name = "type_new"
    hx_trigger_django = "reload"
    modal_form_title = _("Fund")
    success_url = reverse_lazy("savings:tab_funds")


class TypeUpdate(UpdateViewMixin):
    service_class = SavingTypeModelService
    form_class = forms.SavingTypeForm
    url_name = "type_update"
    hx_trigger_django = "reload"
    modal_form_title = _("Fund")
    success_url = reverse_lazy("savings:tab_funds")


class TabPensions(TabViewMixin, ListViewMixin):
    tab = TABS["pensions"]

    def get_queryset(self):
        user = self.request.user
        return PensionModelService(user).year(user.selected_year())


class TabPensionFunds(TabViewMixin, ListViewMixin):
    tab = TABS["pension_funds"]

    def get_queryset(self):
        return PensionTypeModelService(self.request.user).items()
