import contextlib
from datetime import datetime

from django.conf import settings

from .lib import date as lib_date


def years(request):
    _years = lib_date.years(request.user)

    return {"years": _years[::-1]}


def yday(request):
    _year = datetime.now().year

    with contextlib.suppress(AttributeError):
        _year = request.year

    _yday, _ydays = lib_date.yday(_year)

    return {"yday": _yday, "ydays": _ydays}


def context_months(context):
    return {"context_months": lib_date.year_month_list()}


def context_counts_menu(context):
    qs = []

    with contextlib.suppress(AttributeError, ValueError):
        from ..counts.services.model_services import CountTypeModelService
        qs = CountTypeModelService(context.user).objects

    return {"counts_menu": qs}
