from django.shortcuts import render
from django.utils.text import format_lazy

from ..tabs import Tab, Tabs


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
            "tab_url": self.tab.url,
            "reload_trigger": self.tab.reload_trigger,
        }

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        htmx = self.request.htmx
        page = {**context, **self.page_context(), "content": response.rendered_content}
        template = self.page_template

        # base.html reloads on Back, so this runs only if htmx swaps a restore again
        if htmx and not htmx.history_restore_request:
            template = self.fragment_template

        return render(self.request, template, page)

    def page_context(self) -> dict:
        return {
            "page_title": format_lazy("{} | {}", self.app_title, self.tab.title),
            "tabs": [(tab, tab.url) for tab in self.tabs],
        }
