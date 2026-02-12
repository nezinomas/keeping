from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .lib.date import years
from .lib.utils import get_safe_redirect
from .mixins.views import TemplateViewMixin, http_htmx_response
from .services import signals_service
from .tests.utils import timer


@login_required()
def set_year(request, year):
    user = request.user
    if year in years(user):
        user.year = year
        user.save()

    return redirect(get_safe_redirect(request, request.META.get("HTTP_REFERER")))


class RegenerateBalances(TemplateViewMixin):
    # @timer(7)
    def get(self, request, *args, **kwargs):
        _type = request.GET.get("type")
        _types = ["accounts", "savings", "pensions"]

        hx_trigger_name = "afterSignal"
        if _type and _type in _types:
            _types = [_type]
            hx_trigger_name += _type.title()

        for _type in _types:
            getattr(signals_service, f"sync_{_type}")(instance=None, user=request.user)

        return http_htmx_response(hx_trigger_name)


class ModalImage(TemplateViewMixin):
    template_name = "core/modal_image.html"
