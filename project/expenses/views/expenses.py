from datetime import datetime

from django.db.models import CharField, F, Value
from django.db.models.functions import Cast, Concat
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from ...core.lib.convert_price import ConvertToCents
from ...core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    SearchViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from .. import forms, models
from ..services.model_services import (
    ExpenseModelService,
    ExpenseNameModelService,
)


class GetMonthMixin:
    def get_month(self):
        month = self.kwargs.get("month")
        now = datetime.now().month

        try:
            month = int(month)
        except (ValueError, TypeError):
            month = now

        return month


class Index(GetMonthMixin, TemplateViewMixin):
    template_name = "expenses/index.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"month": self.get_month()}


class Lists(GetMonthMixin, ListViewMixin):
    model = models.Expense

    def get_queryset(self):
        month = self.get_month()
        user = self.request.user
        qs = ExpenseModelService(user).year(user.year)

        if month in range(1, 13):
            qs = qs.filter(date__month=month)

        # 1. Dummy URL using a unique placeholder ID
        dummy_id = 0

        update_pattern = reverse("expenses:update", args=[dummy_id])
        delete_pattern = reverse("expenses:delete", args=[dummy_id])

        # 2. Split the URL around the ID
        # prefix becomes "/expenses/update/"
        # suffix becomes "/"
        u_prefix, u_suffix = update_pattern.split(str(dummy_id))
        d_prefix, d_suffix = delete_pattern.split(str(dummy_id))

        return (
            qs
            .annotate(
                url_update=Concat(
                    Value(u_prefix),
                    Cast("id", output_field=CharField()),
                    Value(u_suffix),
                    output_field=CharField(),
                ),
                url_delete=Concat(
                    Value(d_prefix),
                    Cast("id", output_field=CharField()),
                    Value(d_suffix),
                    output_field=CharField(),
                ),
            )
            .order_by("-date", "expense_type__title", F("expense_name__title").asc())
            .values(
                "id",
                "date",
                "account__title",
                "expense_type__pk",
                "expense_type__title",
                "expense_name__title",
                "price",
                "quantity",
                "remark",
                "attachment",
                "exception",
                "url_update",
                "url_delete",
            )
        )

    def get_context_data(self, **kwargs):
        month = self.get_month()

        notice = _("There are no records for month <b>%(month)s</b>.") % {
            "month": month
        }
        if month == 13 or not month:
            notice = _("No records in <b>%(year)s</b>.") % {
                "year": self.request.user.year
            }

        context = {"notice": notice}
        return super().get_context_data(**kwargs) | context


class New(CreateViewMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    success_url = reverse_lazy("expenses:list")
    hx_trigger_form = "reload"
    modal_form_title = _("Expenses")
    template_name = "expenses/expense_form.html"


class Update(ConvertToCents, UpdateViewMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    success_url = reverse_lazy("expenses:list")
    hx_trigger_django = "reload"
    modal_form_title = _("Expenses")
    template_name = "expenses/expense_form.html"


class Delete(DeleteViewMixin):
    model = models.Expense
    success_url = reverse_lazy("expenses:list")
    modal_form_title = _("Delete expense")


class Search(SearchViewMixin):
    template_name = "expenses/expense_list.html"
    search_method = "search_expenses"
    per_page = 50


class LoadExpenseName(ListViewMixin):
    template_name = "core/dropdown.html"
    object_list = []

    def get(self, request, *args, **kwargs):
        expense_type_pk = request.GET.get("expense_type")

        try:
            expense_type_pk = int(expense_type_pk)
        except (ValueError, TypeError):
            expense_type_pk = None

        if expense_type_pk:
            self.object_list = (
                ExpenseNameModelService(request.user)
                .year(request.user.year)
                .filter(parent=expense_type_pk)
            )
        return self.render_to_response({"object_list": self.object_list})
