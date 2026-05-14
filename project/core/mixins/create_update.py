from django_htmx.http import HttpResponseClientRedirect, trigger_client_event


class CreateUpdateMixin:
    hx_trigger_django = None
    hx_trigger_form = None
    hx_redirect = None

    def get_hx_trigger_django(self):
        # triggers Htmx to reload container on Submit button click
        # triggering happens many times
        return self.hx_trigger_django or None

    def get_hx_trigger_form(self):
        # triggers Htmx to reload container on Close button click
        # triggering happens once
        return self.hx_trigger_form or None

    def get_hx_redirect(self):
        return self.hx_redirect

    def get_context_data(self, **kwargs):
        context = {
            "modal_form_title": getattr(self, "modal_form_title", None),
            "modal_body_css_class": getattr(self, "modal_body_css_class", ""),
            "form_action": self.form_action,
            "url": self.url,
            "hx_trigger_form": self.get_hx_trigger_form(),
        }
        return super().get_context_data(**kwargs) | context

    def form_valid(self, form, **kwargs):
        response = super().form_valid(form)

        if not self.request.htmx:
            return response

        self.hx_redirect = self.get_hx_redirect()

        if self.hx_redirect:
            # close form and redirect to url with hx_trigger_django
            return HttpResponseClientRedirect(self.hx_redirect)

        # close form and reload container
        response.status_code = 204
        if trigger := self.get_hx_trigger_django():
            trigger_client_event(response=response, name=trigger, params={})
        return response
