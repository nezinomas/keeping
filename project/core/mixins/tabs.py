from functools import cached_property
from urllib.parse import urlencode

from django.shortcuts import render
from django.utils.text import format_lazy

from ..lib.utils import wants_fragment
from ..tabs import Tab, Tabs


def sorted_tab_urls(tab: Tab, order: str) -> dict:
    # the header links add their own order; a save reloads the one shown
    return {"sort_url": tab.url, "tab_url": f"{tab.url}?{urlencode({'order': order})}"}


class TabViewMixin:
    tabs: Tabs
    default_tab: Tab
    app_title: str
    fragment_template = "core/tab_fragment.html"
    page_template = ""

    @property
    def tab(self) -> Tab:
        return self.default_tab

    def get_template_names(self):
        return [self.tab.template_name]

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "tab": self.tab.name,
            "tab_url": self.tab_url_of(self.tab),
            "reload_trigger": self.tab.reload_trigger,
        }

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        page = {**context, **self.page_context(), "content": response.rendered_content}
        template = self.page_template

        # base.html reloads on Back, so this runs only if htmx swaps a restore again
        if wants_fragment(self.request):
            template = self.fragment_template

        return render(self.request, template, page)

    def page_context(self) -> dict:
        return {
            "page_title": format_lazy("{} | {}", self.app_title, self.tab.title),
            "tabs": [(tab, self.tab_url_of(tab)) for tab in self.tabs],
        }

    def tab_url_of(self, tab: Tab) -> str:
        return tab.url


class ClosedFoldTabMixin:
    """A Closed fold's tab: the owners open in the viewed year, then those closed
    before it under `closed_key`."""

    service_class: type
    closed_key: str
    order: tuple[str, ...]

    @cached_property
    def service(self):
        return self.service_class(self.request.user)

    @cached_property
    def year(self) -> int:
        return self.request.user.selected_year()

    def get_queryset(self):
        return self.service.items_in(self.year).order_by(*self.order)

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            self.closed_key: self.service.closed_before(self.year),
        }
