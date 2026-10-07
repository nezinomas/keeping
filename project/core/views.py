from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from ..bookkeeping import balance_sources
from .lib.date import years
from .lib.utils import get_safe_redirect, http_htmx_response
from .mixins.views import TemplateViewMixin


@login_required()
def set_year(request, year):
    user = request.user
    if year in years(user):
        user.year = year
        user.save()

    return redirect(get_safe_redirect(request, request.META.get("HTTP_REFERER")))


class RegenerateBalances(TemplateViewMixin):
    def get(self, request, *args, **kwargs):
        balances = {
            "accounts": (balance_sources.sync_accounts, "afterSignalAccounts"),
            "savings": (balance_sources.sync_savings, "afterSignalSavings"),
            "pensions": (balance_sources.sync_pensions, "afterSignalPensions"),
        }
        syncs = [sync for sync, _ in balances.values()]
        hx_trigger_name = "afterSignal"

        if (kind := request.GET.get("type")) in balances:
            sync, hx_trigger_name = balances[kind]
            syncs = [sync]

        for sync in syncs:
            sync(request.user)

        return http_htmx_response(hx_trigger_name)


class ModalImage(TemplateViewMixin):
    template_name = "core/modal_image.html"
