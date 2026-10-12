from datetime import date

from .lib import date as lib_date


def years(request):
    if not request.user.is_authenticated:
        return {"years": []}

    return {"years": lib_date.years(request.user)[::-1]}


def yday(request):
    year = date.today().year
    if request.user.is_authenticated:
        year = request.user.year

    _yday, _ydays = lib_date.yday(year)

    return {"yday": _yday, "ydays": _ydays}


def context_months(request):
    if not request.user.is_authenticated:
        return {"context_months": []}

    return {"context_months": lib_date.year_month_list(request.user.year)}


def csp_nonce(request):
    return {"csp_nonce": getattr(request, "_csp_nonce", "")}
