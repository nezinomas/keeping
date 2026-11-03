from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.utils import int_or_zero
from ..core.mixins.views import (
    CreateViewMixin,
    ListViewMixin,
    UpdateViewMixin,
)
from ..transactions.services.account_scope import OPEN
from . import forms, models
from .services.model_services import AccountModelService

SAVED_URL = reverse_lazy("transactions:tab_accounts", args=[OPEN])


class New(CreateViewMixin):
    form_class = forms.AccountForm
    success_url = SAVED_URL
    hx_trigger_django = "reload"
    modal_form_title = _("Account")


class Update(UpdateViewMixin):
    model = models.Account
    form_class = forms.AccountForm
    success_url = SAVED_URL
    hx_trigger_django = "reload"
    modal_form_title = _("Account")

    def get_queryset(self):
        return AccountModelService(self.request.user).all()


class LoadAccount(ListViewMixin):
    template_name = "core/dropdown.html"

    def get(self, request, *args, **kwargs):
        pk = int_or_zero(request.GET.get("from_account"))
        if not pk:
            return self.render_to_response({"object_list": []})

        items = AccountModelService(request.user).items().exclude(pk=pk)
        return self.render_to_response({"object_list": items})
