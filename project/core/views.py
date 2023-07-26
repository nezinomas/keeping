from urllib.parse import urlparse

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import resolve

from . import signals
from .lib.date import years
from .mixins.views import TemplateViewMixin, httpHtmxResponse
from .tests.utils import timer


@login_required()
def set_year(request, year):
    if year in years():
        user = request.user
        user.year = year
        user.save()

    parsed = urlparse(request.META.get("HTTP_REFERER"))

    return redirect(parsed.path) if resolve(parsed.path) else redirect("/")


class RegenerateBalances(TemplateViewMixin):
    # @timer(7)
    def get(self, request, *args, **kwargs):
        _type = request.GET.get("type")
        _types = ["accounts", "savings", "pensions"]
        _kwargs = {
            "sender": None,
            "instance": None,
        }

        hx_trigger_name = "afterSignal"
        if _type and _type in _types:
            _types = [_type]
            hx_trigger_name += _type.title()

        for _type in _types:
            getattr(signals, f"{_type}_signal")(**_kwargs)

        return httpHtmxResponse(hx_trigger_name)
