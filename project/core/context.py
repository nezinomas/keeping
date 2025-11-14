import contextlib
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils.safestring import mark_safe

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
    file = None

    with contextlib.suppress(AttributeError):
        journal_pk = context.user.journal.pk
        file = Path(settings.MEDIA_ROOT, str(journal_pk), "menu.html")

    menu = file.read_text(encoding="utf-8") if file and file.exists() else ""

    return {"counts_menu": mark_safe(menu)}
