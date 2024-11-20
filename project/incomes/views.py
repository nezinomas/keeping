from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from ..core.lib.convert_price import ConvertToCents
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    SearchViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from . import forms, models


class Index(TemplateViewMixin):
    template_name = "incomes/index.html"


class Lists(ListViewMixin):
    model = models.Income

    def get_queryset(self):
        year = self.request.user.year
        return models.Income.objects.year(year).order_by("-date", "price")


class New(CreateViewMixin):
    model = models.Income
    form_class = forms.IncomeForm
    success_url = reverse_lazy("incomes:list")
    hx_trigger_form = "reload"


class Update(ConvertToCents, UpdateViewMixin):
    model = models.Income
    form_class = forms.IncomeForm
    success_url = reverse_lazy("incomes:list")
    hx_trigger_django = "reload"


class Delete(DeleteViewMixin):
    model = models.Income
    success_url = reverse_lazy("incomes:list")
    hx_trigger_django = "reload"
    template_name = "cotton/generic_delete_form.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {"title": _("Delete incomes")}


class TypeLists(ListViewMixin):
    model = models.IncomeType


class TypeNew(CreateViewMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm
    hx_trigger_django = "afterType"
    url = reverse_lazy("incomes:type_new")
    success_url = reverse_lazy("incomes:type_list")


class TypeUpdate(UpdateViewMixin):
    model = models.IncomeType
    form_class = forms.IncomeTypeForm
    hx_trigger_django = "afterType"
    success_url = reverse_lazy("incomes:type_list")


class Search(SearchViewMixin):
    template_name = "incomes/income_list.html"
    search_method = "search_incomes"
    per_page = 50
