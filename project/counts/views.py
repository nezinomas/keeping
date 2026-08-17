from django.db.models import Min
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

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
from .lib.notices import NO_RECORDS, notice_state
from .lib.views_helper import CountTypetObjectMixin, CountUrlMixin
from .models import Count
from .services.cards import HistoryCards, OverviewCards, PeriodicityCards
from .services.counter_life import CounterLife
from .services.model_services import CountModelService, CountTypeModelService
from .tabs import DEFAULT_TAB, TABS, CountTab


class Redirect(RedirectViewMixin):
    def get_redirect_url(self, *args, **kwargs):
        if qs := CountTypeModelService(self.request.user).objects.first():
            return reverse("counts:index", kwargs={"slug": qs.slug})

        return reverse("counts:empty")


class Empty(TemplateViewMixin):
    template_name = "counts/empty.html"


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

    def _life(self) -> CounterLife:
        return CounterLife.read(self.request.user, self.object.slug)


class TabIndex(TabViewMixin, TemplateViewMixin):
    tab = CountTab.resolve("index")

    def get_context_data(self, **kwargs):
        life = self._life()

        return {
            **super().get_context_data(**self.kwargs),
            **services.index.load_index_service(life),
            "cards": OverviewCards.build(life),
        }


class TabPeriodicity(TabViewMixin, TemplateViewMixin):
    tab = CountTab.resolve("periodicity")

    def get_context_data(self, **kwargs):
        life = self._life()

        return {
            **super().get_context_data(**self.kwargs),
            **services.index.load_periodicity_service(life),
            "cards": PeriodicityCards.build(life),
        }


class TabData(TabViewMixin, ListViewMixin):
    tab = CountTab.resolve("data")
    model = Count

    def get_queryset(self):
        year = self.request.user.year
        slug = self.kwargs.get("slug")

        return CountModelService(self.request.user).year(year=year, count_type=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**self.kwargs)
        has_records = (
            CountModelService(self.request.user)
            .items(count_type=self.kwargs.get("slug"))
            .exists()
        )

        return {
            **context,
            "notice": notice_state(has_records, bool(context["object_list"])),
            "notice_year": self.request.user.year,
        }


class TabHistory(TabViewMixin, TemplateViewMixin):
    tab = CountTab.resolve("history")

    def get_context_data(self, **kwargs):
        life = self._life()
        context = services.index.load_history_service(life)

        return {
            **super().get_context_data(**self.kwargs),
            **context,
            "cards": HistoryCards.build(life),
            "notice": "" if context["records"] else NO_RECORDS,
        }


class New(CountUrlMixin, CreateViewMixin):
    service_class = CountModelService
    form_class = CountForm
    modal_form_title = _("Counter")

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["counter_type"] = self.kwargs.get("slug")
        return super().get_form(data, files, **kwargs)

    def get_hx_trigger_django(self):
        return CountTab.resolve(self.kwargs.get("tab"), default="data").reload_trigger

    def url(self):
        count_type = self.kwargs.get("slug")
        tab = CountTab.resolve(self.kwargs.get("tab")).name

        return reverse_lazy("counts:new", kwargs={"slug": count_type, "tab": tab})


class Update(CountUrlMixin, UpdateViewMixin):
    service_class = CountModelService
    form_class = CountForm
    hx_trigger_django = "reloadData"
    modal_form_title = _("Counter")


class Delete(CountUrlMixin, DeleteViewMixin):
    service_class = CountModelService
    hx_trigger_django = "reloadData"
    modal_form_title = _("Delete record")


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

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "delete_warning": self._warning(),
            "delete_confirm": self.object.title,
            "delete_confirm_label": _("Type the counter's title to confirm"),
        }

    # a disabled button is a speed bump; the refusal has to be the server's
    def post(self, *args, **kwargs):
        self.object = self.get_object()

        if self.request.POST.get("confirm", "") != self.object.title:
            return self.render_to_response(self.get_context_data())

        return super().post(*args, **kwargs)

    def _warning(self) -> str:
        records = CountModelService(self.request.user).items(
            count_type=self.object.slug
        )
        first = records.aggregate(first=Min("date"))["first"]

        if not first:
            return ""

        return _(
            "Deleting %(counter)s also deletes %(count)s records made since %(year)s."
        ) % {
            "counter": self.object.title,
            "count": records.count(),
            "year": first.year,
        }
