from django_htmx.http import HttpResponseClientRedirect

from ..lib.utils import http_htmx_response


class DeleteMixin:
    hx_trigger_django = "reload"
    hx_redirect = None

    def get_hx_trigger_django(self):
        return self.hx_trigger_django

    def get_hx_redirect(self):
        return self.hx_redirect

    def get_context_data(self, **kwargs):
        context = {
            "url": self.url,
            "modal_form_title": self.modal_form_title,
        }
        return super().get_context_data(**kwargs) | context

    def post(self, *args, **kwargs):
        super().post(*args, **kwargs)

        if hx_redirect := self.get_hx_redirect():
            return HttpResponseClientRedirect(hx_redirect)

        return http_htmx_response(self.get_hx_trigger_django())