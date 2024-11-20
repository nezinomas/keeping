from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..accounts import views as accounts_views
from ..core.lib.convert_price import ConvertToCents
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
    rendered_content,
)
from . import forms, models


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
            self.object_list = models.SavingType.objects.items().exclude(pk=pk)

        return self.render_to_response({"object_list": self.object_list})


class Lists(ListViewMixin):
    model = models.Transaction

    def get_queryset(self):
        return models.Transaction.objects.year(year=self.request.user.year)


class New(CreateViewMixin):
    model = models.Transaction
    form_class = forms.TransactionForm
    hx_trigger_form = "afterTransaction"
    success_url = reverse_lazy("transactions:list")


class Update(ConvertToCents, UpdateViewMixin):
    model = models.Transaction
    form_class = forms.TransactionForm
    hx_trigger_django = "afterTransaction"
    success_url = reverse_lazy("transactions:list")


class Delete(DeleteViewMixin):
    model = models.Transaction
    hx_trigger_django = "afterTransaction"
    success_url = reverse_lazy("transactions:list")
    template_name = "core/generic_delete_form.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"title": _("Delete transaction")}


class SavingsCloseLists(ListViewMixin):
    model = models.SavingClose

    def get_queryset(self):
        return models.SavingClose.objects.year(year=self.request.user.year)


class SavingsCloseNew(CreateViewMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm
    hx_trigger_form = "afterClose"

    url = reverse_lazy("transactions:savings_close_new")
    success_url = reverse_lazy("transactions:savings_close_list")


class SavingsCloseUpdate(ConvertToCents, UpdateViewMixin):
    model = models.SavingClose
    form_class = forms.SavingCloseForm
    hx_trigger_django = "afterClose"
    success_url = reverse_lazy("transactions:savings_close_list")


class SavingsCloseDelete(DeleteViewMixin):
    model = models.SavingClose
    hx_trigger_django = "afterClose"
    success_url = reverse_lazy("transactions:savings_close_list")
    template_name = "core/generic_delete_form.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"title": _("Delete transaction")}


class SavingsChangeLists(ListViewMixin):
    model = models.SavingChange

    def get_queryset(self):
        return models.SavingChange.objects.year(year=self.request.user.year)


class SavingsChangeNew(CreateViewMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm
    hx_trigger_form = "afterChange"

    success_url = reverse_lazy("transactions:savings_change_list")
    url = reverse_lazy("transactions:savings_change_new")


class SavingsChangeUpdate(ConvertToCents, UpdateViewMixin):
    model = models.SavingChange
    form_class = forms.SavingChangeForm
    hx_trigger_django = "afterChange"
    success_url = reverse_lazy("transactions:savings_change_list")


class SavingsChangeDelete(DeleteViewMixin):
    model = models.SavingChange
    hx_trigger_django = "afterChange"
    success_url = reverse_lazy("transactions:savings_change_list")
    template_name = "core/generic_delete_form.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"title": _("Delete transaction")}
