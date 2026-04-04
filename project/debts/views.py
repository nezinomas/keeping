from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import ConvertPriceMixin
from ..core.lib.utils import rendered_content
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from . import forms, models
from .services.model_services import DebtModelService, DebtReturnModelService


class AddDebtTypeMixin:
    def get_form_kwargs(self, **kwargs):
        kwargs["debt_type"] = self.kwargs.get("debt_type")
        return super().get_form_kwargs(**kwargs)


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
    template_name = "debts/debt_list.html"

    def get_queryset(self):
        user = self.request.user
        return DebtModelService(user, self.kwargs["debt_type"]).year(user.year)


class DebtNew(AddDebtTypeMixin, DebtMixin, CreateViewMixin):
    service_class = DebtModelService
    form_class = forms.DebtForm
    modal_form_title = _("Debt")

    def url(self):
        debt_type = self.kwargs.get("debt_type")
        return reverse_lazy("debts:new", kwargs={"debt_type": debt_type})


class DebtUpdate(ConvertPriceMixin, AddDebtTypeMixin, DebtMixin, UpdateViewMixin):
    service_class = DebtModelService
    form_class = forms.DebtForm
    modal_form_title = _("Debt")

    def get_queryset(self):
        return DebtModelService(self.request.user, self.kwargs["debt_type"]).objects

    def url(self):
        return (
            reverse_lazy(
                f"debts:update",
                kwargs={"pk": self.object.pk, "debt_type": self.kwargs["debt_type"]},
            )
            if self.object
            else None
        )


class DebtDelete(AddDebtTypeMixin, DebtMixin, DeleteViewMixin):
    service_class = DebtModelService
    modal_form_title = _("Delete debt")

    def get_queryset(self):
        return DebtModelService(self.request.user, self.kwargs["debt_type"]).objects

    def url(self):
        return (
            reverse_lazy(
                f"debts:delete",
                kwargs={"pk": self.object.pk, "debt_type": self.kwargs["debt_type"]},
            )
            if self.object
            else None
        )


class DebtReturnLists(ListViewMixin):
    template_name = "debts/debtreturn_list.html"
    service_class = DebtReturnModelService

    def get_queryset(self):
        user = self.request.user
        return DebtReturnModelService(user, self.kwargs["debt_type"]).year(user.year)


class DebtReturnNew(AddDebtTypeMixin, DebtReturnMixin, CreateViewMixin):
    service_class = DebtReturnModelService
    form_class = forms.DebtReturnForm
    modal_form_title = _("Debt repayment")

    def url(self):
        debt_type = self.kwargs.get("debt_type")
        return reverse_lazy("debts:return_new", kwargs={"debt_type": debt_type})


class DebtReturnUpdate(
    ConvertPriceMixin, AddDebtTypeMixin, DebtReturnMixin, UpdateViewMixin
):
    service_class = DebtReturnModelService
    form_class = forms.DebtReturnForm
    modal_form_title = _("Debt repayment")

    def get_queryset(self):
        return DebtReturnModelService(
            self.request.user, self.kwargs["debt_type"]
        ).objects

    def url(self):
        return (
            reverse_lazy(
                "debts:return_update",
                kwargs={"pk": self.object.pk, "debt_type": self.kwargs["debt_type"]},
            )
            if self.object
            else None
        )


class DebtReturnDelete(AddDebtTypeMixin, DebtReturnMixin, DeleteViewMixin):
    service_class = DebtReturnModelService
    modal_form_title = _("Delete debt repayment")

    def get_queryset(self):
        return DebtReturnModelService(
            self.request.user, self.kwargs["debt_type"]
        ).objects

    def url(self):
        return (
            reverse_lazy(
                "debts:return_delete",
                kwargs={"pk": self.object.pk, "debt_type": self.kwargs["debt_type"]},
            )
            if self.object
            else None
        )
