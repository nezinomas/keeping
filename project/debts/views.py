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
    model = models.Debt

    def get_queryset(self):
        user = self.request.user
        return DebtModelService(user, self.kwargs["debt_type"]).year(user.year)


class DebtNew(AddDebtTypeMixin, DebtMixin, CreateViewMixin):
    model = models.Debt
    form_class = forms.DebtForm
    modal_form_title = _("Debt")

    def url(self):
        debt_type = self.kwargs.get("debt_type")
        return reverse_lazy("debts:new", kwargs={"debt_type": debt_type})


class DebtUpdate(ConvertToCents, AddDebtTypeMixin, DebtMixin, UpdateViewMixin):
    model = models.Debt
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
    model = models.Debt
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
    model = models.DebtReturn

    def get_queryset(self):
        user = self.request.user
        return DebtReturnModelService(user, self.kwargs["debt_type"]).year(user.year)


class DebtReturnNew(AddDebtTypeMixin, DebtReturnMixin, CreateViewMixin):
    model = models.DebtReturn
    form_class = forms.DebtReturnForm
    modal_form_title = _("Debt repayment")

    def url(self):
        debt_type = self.kwargs.get("debt_type")
        return reverse_lazy("debts:return_new", kwargs={"debt_type": debt_type})


class DebtReturnUpdate(
    ConvertToCents, AddDebtTypeMixin, DebtReturnMixin, UpdateViewMixin
):
    model = models.DebtReturn
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
    model = models.DebtReturn
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