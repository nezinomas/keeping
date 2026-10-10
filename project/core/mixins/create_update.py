from django_htmx.http import HttpResponseClientRedirect, trigger_client_event


class CreateUpdateMixin:
    # fired on every save; the form's trigger fires once, when the modal closes
    hx_trigger_django = ""
    hx_trigger_form = ""
    hx_redirect = ""
    modal_form_title = ""

    def get_hx_trigger_django(self):
        return self.hx_trigger_django

    def get_hx_trigger_form(self):
        return self.hx_trigger_form

    def get_hx_redirect(self):
        return self.hx_redirect

    def get_context_data(self, **kwargs):
        context = {
            "modal_form_title": self.modal_form_title,
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

        if hx_redirect := self.get_hx_redirect():
            return HttpResponseClientRedirect(hx_redirect)

        response.status_code = 204
        if trigger := self.get_hx_trigger_django():
            trigger_client_event(response=response, name=trigger, params={})
        return response
