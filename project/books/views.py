from typing import cast

from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.paginator import CountlessPaginator
from ..core.mixins.search import PER_PAGE
from ..core.mixins.tabs import TabViewMixin as CoreTabViewMixin
from ..core.mixins.views import (
    CreateViewMixin,
    DeleteViewMixin,
    ListViewMixin,
    SearchViewMixin,
    TemplateViewMixin,
    UpdateViewMixin,
)
from ..users.models import User
from . import forms, services
from .services.model_services import BookModelService, BookTargetModelService
from .services.search import search_books
from .tabs import ALL_RECORDS, TABS, YEAR

# the form cannot know the open scope; an htmx save reloads the tab instead
SAVED_URL = reverse_lazy("books:list", kwargs={"scope": YEAR})


class TabViewMixin(CoreTabViewMixin):
    tabs = TABS
    default_tab = TABS["index"]
    app_title = _("Books")
    page_template = "books/index.html"


class TabIndex(TabViewMixin, TemplateViewMixin):
    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        chart = services.ChartFinished(services.ChartFinishedData(user))

        return {
            **super().get_context_data(**kwargs),
            "cards": services.Cards.build(user, user.selected_year()),
            "chart": chart.context(),
        }


class Lists(ListViewMixin):
    template_name = "books/book_list.html"

    def get_queryset(self):
        user = cast(User, self.request.user)
        service = BookModelService(user)
        if self.scope == ALL_RECORDS:
            return service.objects
        return service.year(user.selected_year())

    @property
    def scope(self) -> str:
        scope = YEAR
        if self.kwargs["scope"] == ALL_RECORDS:
            scope = ALL_RECORDS
        return scope

    def get_context_data(self, **kwargs):
        total = self.object_list.count()
        paginator = CountlessPaginator(
            query=self.object_list, total_records=total, per_page=PER_PAGE
        )
        page_obj, paginator_object = paginator.paging(self.request.GET.get("page", 1))

        context = {
            "object_list": page_obj,
            "url": reverse("books:list", kwargs={"scope": self.scope}),
            "scope": self.scope,
            "countdown_from": total - page_obj.start_index() + 1,
            "paginator_object": paginator_object,
        }

        return super().get_context_data(**kwargs) | context


class TabData(TabViewMixin, Lists):
    tab = TABS["data"]

    def get_context_data(self, **kwargs):
        tab_url = reverse("books:tab_data", kwargs={"scope": self.scope})
        return super().get_context_data(**kwargs) | {"tab_url": tab_url}


class New(CreateViewMixin):
    form_class = forms.BookForm
    hx_trigger_django = "reload"
    modal_form_title = _("New book")
    success_url = SAVED_URL


class Update(UpdateViewMixin):
    service_class = BookModelService
    form_class = forms.BookForm
    hx_trigger_django = "reload"
    modal_form_title = _("Update book")
    success_url = SAVED_URL


class Delete(DeleteViewMixin):
    service_class = BookModelService
    modal_form_title = _("Delete book")
    success_url = SAVED_URL


class Search(SearchViewMixin):
    template_name = "books/book_list.html"
    search_method = staticmethod(search_books)


class TargetNew(CreateViewMixin):
    hx_trigger_django = "reload"
    form_class = forms.BookTargetForm
    url_name = "target_new"
    modal_form_title = _("New goal")


class TargetUpdate(UpdateViewMixin):
    service_class = BookTargetModelService
    hx_trigger_django = "reload"
    form_class = forms.BookTargetForm
    url_name = "target_update"
    modal_form_title = _("Update goal")
