from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

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


class DebtMixin:
    def get_success_url(self):
        debt_type = self.kwargs.get("debt_type")
        return reverse_lazy("debts:list", kwargs={"debt_type": debt_type})

    def get_hx_trigger_django(self):
        debt_type = self.kwargs.get("debt_type")
        return f"after_{debt_type}"


class DebtReturnMixin:
    def get_success_url(self):
        debt_type = self.kwargs.get("debt_type")
        return reverse_lazy("debts:return_list", kwargs={"debt_type": debt_type})

    def get_hx_trigger_django(self):
        debt_type = self.kwargs.get("debt_type")
        return f"after_{debt_type}_return"


class Index(TemplateViewMixin):
    template_name = "debts/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "borrow": rendered_content(
                    self.request, DebtLists, **{"debt_type": "borrow"}
                ),
                "borrow_return": rendered_content(
                    self.request, DebtReturnLists, **{"debt_type": "borrow"}
                ),
                "lend": rendered_content(
                    self.request, DebtLists, **{"debt_type": "lend"}
                ),
                "lend_return": rendered_content(
                    self.request, DebtReturnLists, **{"debt_type": "lend"}
                ),
            }
        )
        return context


class DebtLists(ListViewMixin):
    model = models.Debt

    def get_queryset(self):
        return models.Debt.objects.year(year=self.request.user.year)


class DebtNew(DebtMixin, CreateViewMixin):
    model = models.Debt
    form_class = forms.DebtForm
    template_name = "core/generic_form.html"
    form_title = _("Debt")

    def url(self):
        debt_type = self.kwargs.get("debt_type")
        return reverse_lazy("debts:new", kwargs={"debt_type": debt_type})


class DebtUpdate(ConvertToCents, DebtMixin, UpdateViewMixin):
    model = models.Debt
    form_class = forms.DebtForm
    template_name = "core/generic_form.html"
    form_title = _("Debt")


class DebtDelete(DebtMixin, DeleteViewMixin):
    model = models.Debt
    template_name = "core/generic_delete_form.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"title": _("Delete")}


class DebtReturnLists(ListViewMixin):
    model = models.DebtReturn

    def get_queryset(self):
        return models.DebtReturn.objects.year(year=self.request.user.year)


class DebtReturnNew(DebtReturnMixin, CreateViewMixin):
    model = models.DebtReturn
    form_class = forms.DebtReturnForm
    template_name = "core/generic_form.html"
    form_title = _('Debt repayment')

    def url(self):
        debt_type = self.kwargs.get("debt_type")
        return reverse_lazy("debts:return_new", kwargs={"debt_type": debt_type})


class DebtReturnUpdate(ConvertToCents, DebtReturnMixin, UpdateViewMixin):
    model = models.DebtReturn
    form_class = forms.DebtReturnForm
    template_name = "core/generic_form.html"
    form_title = _('Debt repayment')


class DebtReturnDelete(DebtReturnMixin, DeleteViewMixin):
    model = models.DebtReturn
    template_name = "core/generic_delete_form.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"title": _("Delete")}