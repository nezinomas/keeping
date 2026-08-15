from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.utils import rendered_content
from ..core.lib.year_boundary import YearBoundary
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    RedirectViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from . import services
from .forms import CountForm, CountTypeForm
from .lib.views_helper import (
    CountTypetObjectMixin,
    CountUrlMixin,
    InfoRowData,
)
from .models import Count
from .services.model_services import CountModelService, CountTypeModelService
from .tabs import DEFAULT_TAB, TABS, CountTab


class Redirect(RedirectViewMixin):
    def get_redirect_url(self, *args, **kwargs):
        if qs := CountTypeModelService(self.request.user).objects.first():
            return reverse("counts:index", kwargs={"slug": qs.slug})

        return reverse("counts:empty")


class Empty(TemplateViewMixin):
    template_name = "counts/empty.html"


class InfoRow(CountTypetObjectMixin, TemplateViewMixin):
    template_name = "counts/info_row.html"

    def get_context_data(self, **kwargs):
        super().get_object()

        user = self.request.user
        year = user.year
        week = YearBoundary.for_year(year).weeks_elapsed
        data = InfoRowData(user, self.object.slug)

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


class TabViewMixin(CountTypetObjectMixin):
    tab = DEFAULT_TAB

    def dispatch(self, request, *args, **kwargs):
        self.get_object()

        if not self.object:
            return redirect(reverse("counts:redirect"))

        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [self.tab.template_name]

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**self.kwargs), "tab": self.tab.name}

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        htmx = self.request.htmx

        if htmx and not htmx.history_restore_request:
            return response

        return render(
            self.request,
            "counts/index.html",
            {**context, **self._page(), "content": response.rendered_content},
        )

    def _page(self) -> dict:
        return {
            "object": self.object,
            "tabs": [(tab, tab.url(self.object.slug)) for tab in TABS],
        }


class TabIndex(TabViewMixin, TemplateViewMixin):
    tab = CountTab.resolve("index")

    def get_context_data(self, **kwargs):
        user = self.request.user
        count_type = self.object.slug
        context = services.index.load_index_service(user, count_type)

        return {
            **super().get_context_data(**self.kwargs),
            **context,
            "info_row": rendered_content(
                self.request, InfoRow, **self.kwargs | {"tab": "index"}
            ),
        }


class TabData(TabViewMixin, ListViewMixin):
    tab = CountTab.resolve("data")
    model = Count

    def get_queryset(self):
        year = self.request.user.year
        slug = self.kwargs.get("slug")

        return CountModelService(self.request.user).year(year=year, count_type=slug)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**self.kwargs),
            "info_row": rendered_content(
                self.request, InfoRow, **self.kwargs | {"tab": "data"}
            ),
        }


class TabHistory(TabViewMixin, TemplateViewMixin):
    tab = CountTab.resolve("history")

    def get_context_data(self, **kwargs):
        user = self.request.user
        count_type = self.kwargs.get("slug")
        context = services.index.load_history_service(user, count_type)

        return {
            **super().get_context_data(**self.kwargs),
            **context,
            "info_row": rendered_content(
                self.request,
                InfoRow,
                **self.kwargs | {"tab": "history", "records": context["records"]},
            ),
        }


class New(CountUrlMixin, CreateViewMixin):
    service_class = CountModelService
    form_class = CountForm
    modal_form_title = _("Counter")

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["counter_type"] = self.kwargs.get("slug")
        return super().get_form(data, files, **kwargs)

    def get_hx_trigger_django(self):
        tab = self.kwargs.get("tab")

        if tab in ["index", "data", "history"]:
            return f"reload{tab.title()}"

        return "reloadData"

    def url(self):
        count_type = self.kwargs.get("slug")
        tab = self.kwargs.get("tab")

        if tab not in ["index", "data", "history"]:
            tab = "index"

        return reverse_lazy("counts:new", kwargs={"slug": count_type, "tab": tab})


class Update(CountUrlMixin, UpdateViewMixin):
    service_class = CountModelService
    form_class = CountForm
    hx_trigger_django = "reloadData"
    modal_form_title = _("Counter")


class Delete(CountUrlMixin, DeleteViewMixin):
    service_class = CountModelService
    hx_trigger_django = "reloadData"
    modal_form_title = _("Delete counter")


# -------------------------------------------------------------------------------------
#                                                                           Count Types
# -------------------------------------------------------------------------------------
class TypeUrlMixin:
    def get_hx_redirect(self):
        return self.get_success_url()

    def get_success_url(self):
        slug = self.object.slug
        return reverse_lazy("counts:index", kwargs={"slug": slug})


class TypeNew(TypeUrlMixin, CreateViewMixin):
    service_class = CountTypeModelService
    form_class = CountTypeForm
    url_name = "type_new"
    hx_trigger_django = "afterType"
    modal_form_title = _("Count type")


class TypeUpdate(TypeUrlMixin, UpdateViewMixin):
    service_class = CountTypeModelService
    form_class = CountTypeForm
    url_name = "type_update"
    hx_trigger_django = "afterType"
    modal_form_title = _("Count type")


class TypeDelete(TypeUrlMixin, DeleteViewMixin):
    service_class = CountTypeModelService
    url_name = "type_delete"
    hx_trigger_django = "afterType"
    hx_redirect = reverse_lazy("counts:redirect")
    modal_form_title = _("Delete count type")
