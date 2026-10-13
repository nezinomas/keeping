from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.convert_price import PriceToFloatViewMixin
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
    def url(self):
        # the route's kwargs carry the debt type, and the pk where there is one
        return reverse_lazy(f"debts:{self.url_name}", kwargs=self.kwargs)

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
                    self.request, DebtLists, debt_type=models.Debt.DebtType.BORROW
                ),
                "borrow_return": rendered_content(
                    self.request, DebtReturnLists, debt_type=models.Debt.DebtType.BORROW
                ),
                "lend": rendered_content(
                    self.request, DebtLists, debt_type=models.Debt.DebtType.LEND
                ),
                "lend_return": rendered_content(
                    self.request, DebtReturnLists, debt_type=models.Debt.DebtType.LEND
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
    url_name = "new"
    service_class = DebtModelService
    form_class = forms.DebtForm
    modal_form_title = _("Debt")


class DebtUpdate(PriceToFloatViewMixin, AddDebtTypeMixin, DebtMixin, UpdateViewMixin):
    url_name = "update"
    service_class = DebtModelService
    form_class = forms.DebtForm
    modal_form_title = _("Debt")

    def get_queryset(self):
        return DebtModelService(self.request.user, self.kwargs["debt_type"]).objects


class DebtDelete(AddDebtTypeMixin, DebtMixin, DeleteViewMixin):
    url_name = "delete"
    service_class = DebtModelService
    modal_form_title = _("Delete debt")

    def get_queryset(self):
        return DebtModelService(self.request.user, self.kwargs["debt_type"]).objects


class DebtReturnLists(ListViewMixin):
    template_name = "debts/debtreturn_list.html"
    service_class = DebtReturnModelService

    def get_queryset(self):
        user = self.request.user
        return DebtReturnModelService(user, self.kwargs["debt_type"]).year(user.year)


class DebtReturnNew(AddDebtTypeMixin, DebtReturnMixin, CreateViewMixin):
    url_name = "return_new"
    service_class = DebtReturnModelService
    form_class = forms.DebtReturnForm
    modal_form_title = _("Debt repayment")


class DebtReturnUpdate(
    PriceToFloatViewMixin, AddDebtTypeMixin, DebtReturnMixin, UpdateViewMixin
):
    url_name = "return_update"
    service_class = DebtReturnModelService
    form_class = forms.DebtReturnForm
    modal_form_title = _("Debt repayment")

    def get_queryset(self):
        return DebtReturnModelService(
            self.request.user, self.kwargs["debt_type"]
        ).objects


class DebtReturnDelete(AddDebtTypeMixin, DebtReturnMixin, DeleteViewMixin):
    url_name = "return_delete"
    service_class = DebtReturnModelService
    modal_form_title = _("Delete debt repayment")

    def get_queryset(self):
        return DebtReturnModelService(
            self.request.user, self.kwargs["debt_type"]
        ).objects
