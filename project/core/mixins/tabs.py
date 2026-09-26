from django.shortcuts import render


class TabViewMixin:
    fragment_template = ""
    page_template = ""

    def get_template_names(self):
        return [self.tab.template_name]

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "tab": self.tab.name}

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        htmx = self.request.htmx
        page = {**context, **self.page_context(), "content": response.rendered_content}
        template = self.page_template

        # a Back restore rebuilds the whole page, so it needs the shell too
        if htmx and not htmx.history_restore_request:
            template = self.fragment_template

        return render(self.request, template, page)

    def page_context(self) -> dict:
        return {}
