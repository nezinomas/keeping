from typing import cast

from django.urls import reverse, reverse_lazy
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from ..core.lib.paginator import CountlessPaginator
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
from .tabs import DEFAULT_TAB, TABS, BookTab


def _reading_year(user: User) -> int:
    # User.year is NULL until the first login sets it (Avoid None 3, 5)
    if user.year is None:
        raise ValueError(f"{user} has no year")
    return user.year


class TabViewMixin(CoreTabViewMixin):
    tab = DEFAULT_TAB
    fragment_template = "books/tab_fragment.html"
    page_template = "books/index.html"

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "tab_url": self.tab.url}

    def page_context(self) -> dict:
        return {
            "page_title": format_lazy("{} | {}", _("Books"), self.tab.title),
            "tabs": [(tab, tab.url) for tab in TABS],
        }


class TabIndex(TabViewMixin, TemplateViewMixin):
    tab = BookTab.resolve("index")

    def get_context_data(self, **kwargs):
        user = cast(User, self.request.user)
        chart = services.ChartFinished(services.ChartFinishedData(user))

        return {
            **super().get_context_data(**kwargs),
            "cards": services.Cards.build(user, _reading_year(user)),
            "chart": chart.context(),
        }


class Lists(ListViewMixin):
    template_name = "books/book_list.html"
    service_class = BookModelService
    per_page = 50

    def get_queryset(self):
        user = cast(User, self.request.user)
        service = BookModelService(user)
        return service.objects if self.scope else service.year(_reading_year(user))

    @property
    def scope(self) -> str:
        scope = ""
        if self.request.GET.get("scope") == "all":
            scope = "all"
        return scope

    def get_context_data(self, **kwargs):
        sql = self.get_queryset()
        paginator = CountlessPaginator(
            query=sql, total_records=sql.count(), per_page=self.per_page
        )
        page_obj, paginator_object = paginator.paging(self.request.GET.get("page", 1))

        context = {
            "object_list": page_obj,
            "url": reverse("books:list"),
            "scope": self.scope,
            "first_item": paginator.count - page_obj.start_index() + 1,
            "paginator_object": paginator_object,
        }

        return super().get_context_data(**kwargs) | context


class TabData(TabViewMixin, Lists):
    tab = BookTab.resolve("data")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.scope:
            context["tab_url"] = f"{self.tab.url}?scope={self.scope}"
        return context


class New(CreateViewMixin):
    service_class = BookModelService
    form_class = forms.BookForm
    hx_trigger_django = "reload"
    modal_form_title = _("New book")
    success_url = reverse_lazy("books:list")


class Update(UpdateViewMixin):
    service_class = BookModelService
    form_class = forms.BookForm
    hx_trigger_django = "reload"
    modal_form_title = _("Update book")
    success_url = reverse_lazy("books:list")


class Delete(DeleteViewMixin):
    service_class = BookModelService
    modal_form_title = _("Delete book")
    success_url = reverse_lazy("books:list")


class Search(SearchViewMixin):
    template_name = "books/book_list.html"
    per_page = 50
    search_method = staticmethod(search_books)


class TargetNew(CreateViewMixin):
    service_class = BookTargetModelService
    hx_trigger_django = "afterTarget"
    form_class = forms.BookTargetForm
    url_name = "target_new"
    modal_form_title = _("New goal")


class TargetUpdate(UpdateViewMixin):
    service_class = BookTargetModelService
    hx_trigger_django = "afterTarget"
    form_class = forms.BookTargetForm
    url_name = "target_update"
    modal_form_title = _("Update goal")
