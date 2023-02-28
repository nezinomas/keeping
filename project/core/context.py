import contextlib
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils.safestring import mark_safe

from ..core.lib import utils
from .lib.date import yday as Yday
from .lib.date import year_month_list
from .lib.date import years as Year


def years(context):
    _years = Year()

    return {"years": _years[::-1]}


def yday(context):
    _year = datetime.now().year

    with contextlib.suppress(AttributeError):
        _year = utils.get_user().year

    _yday, _ydays = Yday(_year)

    return {"yday": _yday, "ydays": _ydays}


def context_months(context):
    return {"context_months": year_month_list()}


def context_counts_menu(context):
    file = None

    with contextlib.suppress(AttributeError):
        journal_pk = context.user.journal.pk
        file = Path(settings.MEDIA_ROOT, str(journal_pk), "menu.html")

    menu = file.read_text(encoding="utf-8") if file and file.exists() else ""

    return {"counts_menu": mark_safe(menu)}
