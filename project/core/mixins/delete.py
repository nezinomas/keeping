from django_htmx.http import HttpResponseClientRedirect

from ..lib.utils import http_htmx_response
from .htmx import HxResponseMixin


class DeleteMixin(HxResponseMixin):
    hx_trigger_django = "reload"

    url = ""
    modal_form_title = ""

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
