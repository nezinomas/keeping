from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from ..core.lib.date import weeknumber
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    RedirectViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
    rendered_content,
)
from . import services
from .forms import CountForm, CountTypeForm
from .lib.views_helper import CountTypetObjectMixin, InfoRowData
from .models import Count, CountType


class Redirect(RedirectViewMixin):
    def get_redirect_url(self, *args, **kwargs):
        if qs := CountType.objects.related().first():
            return reverse("counts:index", kwargs={"slug": qs.slug})

        return reverse("counts:empty")


class Empty(TemplateViewMixin):
    template_name = "counts/empty.html"


class InfoRow(CountTypetObjectMixin, TemplateViewMixin):
    template_name = "counts/info_row.html"

    def get_context_data(self, **kwargs):
        super().get_object()

        year = self.request.user.year
        week = weeknumber(year)
        data = InfoRowData(year, self.object.slug)

        context = {
            "object": self.object,
            "tab": self.kwargs.get("tab", "index"),
            "records": self.kwargs.get("records", 0),
            "week": week,
            "total": data.total,
            "ratio": data.total / week,
            "current_gap": data.gap,
        }
        return {**super().get_context_data(**kwargs), **context}


class Index(CountTypetObjectMixin, TemplateViewMixin):
    template_name = "counts/index.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        super().get_object()

        if not self.object:
            return redirect(reverse("counts:redirect"))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        super().get_object()

        context = {
            "tab_content": rendered_content(self.request, TabIndex, **self.kwargs),
        }

        return super().get_context_data(**self.kwargs) | context


class TabIndex(CountTypetObjectMixin, TemplateViewMixin):
    template_name = "counts/tab_index.html"

    def get_context_data(self, **kwargs):
        super().get_object()

        year = self.request.user.year
        count_type = self.object.slug
        context = services.index.load_index_service(year, count_type)

        return {
            **super().get_context_data(**self.kwargs),
            **context,
            "info_row": rendered_content(
                self.request, InfoRow, **self.kwargs | {"tab": "index"}
            ),
        }


class TabData(ListViewMixin):
    model = Count
    template_name = "counts/tab_data.html"

    def get_queryset(self):
        year = self.request.user.year
        slug = self.kwargs.get("slug")

        return Count.objects.year(year=year, count_type=slug)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**self.kwargs),
            "info_row": rendered_content(
                self.request, InfoRow, **self.kwargs | {"tab": "data"}
            ),
        }


class TabHistory(TemplateViewMixin):
    template_name = "counts/tab_history.html"

    def get_context_data(self, **kwargs):
        year = self.request.user.year
        count_type = self.kwargs.get("slug")
        context = services.index.load_history_service(year, count_type)

        return {
            **super().get_context_data(**self.kwargs),
            **context,
            "info_row": rendered_content(
                self.request,
                InfoRow,
                **self.kwargs | {"tab": "history", "records": context["records"]},
            ),
        }


class CountUrlMixin:
    def get_success_url(self):
        slug = self.object.count_type.slug
        return reverse_lazy("counts:tab_data", kwargs={"slug": slug})


class New(CountUrlMixin, CreateViewMixin):
    model = Count
    form_class = CountForm

    def get_hx_trigger_django(self):
        tab = self.kwargs.get("tab")

        if tab in ["index", "data", "history"]:
            return f"reload{tab.title()}"

        return "reloadData"

    def url(self):
        count_type_slug = self.kwargs.get("slug")
        tab = self.kwargs.get("tab")

        if tab not in ["index", "data", "history"]:
            tab = "index"

        return reverse_lazy("counts:new", kwargs={"slug": count_type_slug, "tab": tab})


class Update(CountUrlMixin, UpdateViewMixin):
    model = Count
    form_class = CountForm
    hx_trigger_django = "reloadData"


class Delete(CountUrlMixin, DeleteViewMixin):
    model = Count
    hx_trigger_django = "reloadData"


# ---------------------------------------------------------------------------------------
#                                                                             Count Types
# ---------------------------------------------------------------------------------------
class TypeUrlMixin:
    def get_hx_redirect(self):
        return self.get_success_url()

    def get_success_url(self):
        slug = self.object.slug
        return reverse_lazy("counts:index", kwargs={"slug": slug})


class TypeNew(TypeUrlMixin, CreateViewMixin):
    model = CountType
    form_class = CountTypeForm
    hx_trigger_django = "afterType"
    url = reverse_lazy("counts:type_new")


class TypeUpdate(TypeUrlMixin, UpdateViewMixin):
    model = CountType
    form_class = CountTypeForm
    hx_trigger_django = "afterType"


class TypeDelete(TypeUrlMixin, DeleteViewMixin):
    model = CountType
    hx_trigger_django = "afterType"
    hx_redirect = reverse_lazy("counts:redirect")
