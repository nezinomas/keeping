import contextlib
from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import Resolver404, resolve
from django.utils.http import url_has_allowed_host_and_scheme

from .lib.date import years
from .mixins.views import TemplateViewMixin, http_htmx_response
from .services import signals_service
from .tests.utils import timer


@login_required()
def set_year(request, year):
    user = request.user
    if year in years(user):
        user.year = year
        user.save()

    referer = request.META.get("HTTP_REFERER")

    if not referer:
        return redirect("/")

    parsed = urlparse(referer)
    target_path = parsed.path

    # 1. Check if the URL is safe (belongs to domain)
    # 2. Check if the path actually exists in URLconf
    is_safe = url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )

    with contextlib.suppress(Resolver404):
        if is_safe and resolve(target_path):
            return redirect(target_path)

    return redirect("/")


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
