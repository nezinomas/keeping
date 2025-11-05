from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.mixins.views import (
    CreateViewMixin,
    ListViewMixin,
    UpdateViewMixin,
)
from . import forms, models
from .services.model_services import AccountModelService


class Lists(ListViewMixin):
    model = models.Account

    def get_queryset(self):
        return AccountModelService(self.request.user).all().order_by("closed", "title")


class New(CreateViewMixin):
    model = models.Account
    form_class = forms.AccountForm
    success_url = reverse_lazy("accounts:list")
    url = reverse_lazy("accounts:new")
    hx_trigger_django = "afterAccount"
    modal_form_title = _("Account")


class Update(UpdateViewMixin):
    model = models.Account
    form_class = forms.AccountForm
    success_url = reverse_lazy("accounts:list")
    hx_trigger_django = "afterAccount"
    modal_form_title = _("Account")

    def get_queryset(self):
        return AccountModelService(self.request.user).items()


class LoadAccount(ListViewMixin):
    template_name = "core/dropdown.html"
    object_list = []

    def get(self, request, *args, **kwargs):
        pk = request.GET.get("from_account")

        try:
            pk = int(pk)
        except (ValueError, TypeError):
            pk = None

        if pk:
            self.object_list = (
                AccountModelService(self.request.user).items().exclude(pk=pk)
            )

        return self.render_to_response({"object_list": self.object_list})
