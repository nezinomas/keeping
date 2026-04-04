from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..accounts import views as accounts_views
from ..core.lib.convert_price import ConvertPriceMixin
from ..core.lib.utils import rendered_content
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from ..savings.services.model_services import SavingTypeModelService
from . import forms, models
from .services.model_services import (
    SavingChangeModelService,
    SavingCloseModelService,
    TransactionModelService,
)


class Index(TemplateViewMixin):
    template_name = "transactions/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "transaction": rendered_content(self.request, Lists),
                "saving_close": rendered_content(self.request, SavingsCloseLists),
                "saving_change": rendered_content(self.request, SavingsChangeLists),
                "account": rendered_content(self.request, accounts_views.Lists),
            }
        )
        return context


class LoadSavingType(ListViewMixin):
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
                SavingTypeModelService(request.user).items().exclude(pk=pk)
            )

        return self.render_to_response({"object_list": self.object_list})


class Lists(ListViewMixin):
    template_name = "transactions/transaction_list.html"
    service_class = TransactionModelService

    def get_queryset(self):
        user = self.request.user
        return TransactionModelService(user).year(user.year)


class New(CreateViewMixin):
    service_class = TransactionModelService
    form_class = forms.TransactionForm
    hx_trigger_form = "afterTransaction"
    success_url = reverse_lazy("transactions:list")
    modal_form_title = _("Transaction")


class Update(ConvertPriceMixin, UpdateViewMixin):
    service_class = TransactionModelService
    form_class = forms.TransactionForm
    hx_trigger_django = "afterTransaction"
    success_url = reverse_lazy("transactions:list")
    modal_form_title = _("Transaction")


class Delete(DeleteViewMixin):
    service_class = TransactionModelService
    hx_trigger_django = "afterTransaction"
    success_url = reverse_lazy("transactions:list")
    modal_form_title = _("Delete transaction")


class SavingsCloseLists(ListViewMixin):
    template_name = "transactions/savingclose_list.html"
    service_class = SavingCloseModelService

    def get_queryset(self):
        user = self.request.user
        return SavingCloseModelService(user).year(year=user.year)


class SavingsCloseNew(CreateViewMixin):
    service_class = SavingCloseModelService
    form_class = forms.SavingCloseForm
    hx_trigger_form = "afterClose"
    url_name = "savings_close_new"

    success_url = reverse_lazy("transactions:savings_close_list")
    modal_form_title = _("Fund &rArr; Account")


class SavingsCloseUpdate(ConvertPriceMixin, UpdateViewMixin):
    service_class = SavingCloseModelService
    form_class = forms.SavingCloseForm
    hx_trigger_django = "afterClose"
    url_name = "savings_close_update"

    success_url = reverse_lazy("transactions:savings_close_list")
    modal_form_title = _("Fund &rArr; Account")


class SavingsCloseDelete(DeleteViewMixin):
    service_class = SavingCloseModelService
    hx_trigger_django = "afterClose"
    url_name = "savings_close_delete"

    success_url = reverse_lazy("transactions:savings_close_list")
    modal_form_title = _("Delete transaction")


class SavingsChangeLists(ListViewMixin):
    template_name = "transactions/savingchange_list.html"
    service_class = SavingChangeModelService

    def get_queryset(self):
        user = self.request.user
        return SavingChangeModelService(user).year(year=user.year)


class SavingsChangeNew(CreateViewMixin):
    service_class = SavingChangeModelService
    form_class = forms.SavingChangeForm
    hx_trigger_form = "afterChange"
    url_name = "savings_change_new"

    success_url = reverse_lazy("transactions:savings_change_list")
    modal_form_title = _("Fund &hArr; Fund")


class SavingsChangeUpdate(ConvertPriceMixin, UpdateViewMixin):
    service_class = SavingChangeModelService
    form_class = forms.SavingChangeForm
    hx_trigger_django = "afterChange"
    url_name = "savings_change_update"

    success_url = reverse_lazy("transactions:savings_change_list")
    modal_form_title = _("Fund &hArr; Fund")


class SavingsChangeDelete(DeleteViewMixin):
    service_class = SavingChangeModelService
    hx_trigger_django = "afterChange"
    url_name = "savings_change_delete"

    success_url = reverse_lazy("transactions:savings_change_list")
    modal_form_title = _("Delete transaction")
