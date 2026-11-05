from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.mixins.views import (
    CreateViewMixin,
    LoadToAccountViewMixin,
    UpdateViewMixin,
)
from . import forms
from .services.model_services import AccountModelService


class AccountMixin:
    form_class = forms.AccountForm
    success_url = reverse_lazy("transactions:tab_accounts")
    hx_trigger_django = "reload"
    modal_form_title = _("Account")


class New(AccountMixin, CreateViewMixin):
    pass


class Update(AccountMixin, UpdateViewMixin):
    service_class = AccountModelService


class LoadAccount(LoadToAccountViewMixin):
    service_class = AccountModelService
