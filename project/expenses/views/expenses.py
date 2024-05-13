from datetime import datetime

from django.db.models import F
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

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


class Lists(GetMonthMixin, ListViewMixin):
    model = models.Expense

    def get_queryset(self):
        month = self.get_month()
        qs = super().get_queryset().year(year=self.request.user.year)

        if month in range(1, 13):
            qs = qs.filter(date__month=month)

        qs = qs.order_by("-date", "expense_type", F("expense_name").asc())

        return qs

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


class Update(ConvertToCents, UpdateViewMixin):
    model = models.Expense
    form_class = forms.ExpenseForm
    success_url = reverse_lazy("expenses:list")
    hx_trigger_django = "reload"


class Delete(DeleteViewMixin):
    model = models.Expense
    success_url = reverse_lazy("expenses:list")
    hx_trigger_django = "reload"


class Search(SearchViewMixin):
    template_name = "expenses/expense_list.html"
    per_page = 50

    search_method = "search_expenses"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        price, quantity = [], []
        for x in context["object_list"]:
            price.append(x.price)
            quantity.append(x.quantity)

        if not price:
            return context

        sum_price = sum(price)
        sum_quantity = sum(quantity)

        context["sum_price"] = sum_price
        context["sum_quantity"] = sum_quantity
        context["average"] = sum_price / sum_quantity

        return context


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
                models.ExpenseName.objects.related()
                .filter(parent=expense_type_pk)
                .year(request.user.year)
            )
        return self.render_to_response({"object_list": self.object_list})
