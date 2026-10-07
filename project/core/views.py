from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .lib.date import years
from .lib.utils import get_safe_redirect, http_htmx_response
from .mixins.views import TemplateViewMixin
from .services import signals_service
from .services.signals_service import BalanceKind


@login_required()
def set_year(request, year):
    user = request.user
    if year in years(user):
        user.year = year
        user.save()

    return redirect(get_safe_redirect(request, request.META.get("HTTP_REFERER")))


class RegenerateBalances(TemplateViewMixin):
    def get(self, request, *args, **kwargs):
        kinds = list(BalanceKind)
        hx_trigger_name = "afterSignal"

        if request.GET.get("type") in kinds:
            kinds = [BalanceKind(request.GET["type"])]
            hx_trigger_name = kinds[0].trigger

        for kind in kinds:
            signals_service.sync(kind, request.user)

        return http_htmx_response(hx_trigger_name)


class ModalImage(TemplateViewMixin):
    template_name = "core/modal_image.html"
