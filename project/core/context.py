from datetime import date

from .lib import date as lib_date


def years(request):
    if not request.user.is_authenticated:
        return {"years": []}

    return {"years": lib_date.years(request.user, date.today())[::-1]}


def yday(request):
    today = date.today()
    year = today.year
    if request.user.is_authenticated:
        year = request.user.selected_year()

    _yday, _ydays = lib_date.yday(year, today)

    return {"yday": _yday, "ydays": _ydays}


def context_months(request):
    if not request.user.is_authenticated:
        return {"context_months": []}

    return {"context_months": lib_date.year_month_list(request.user.selected_year())}


def _exact(path):
    return lambda request_path: request_path == path


def _within(fragment, excluding=()):
    return lambda request_path: (
        fragment in request_path
        and not any(other in request_path for other in excluding)
    )


# a ledger's url also appears inside the Charts, Plans and Detailed urls
LEDGER_ELSEWHERE = ("/summary/", "/plans/", "/detailed/")

NAV_RULES = (
    ("bookkeeping", _exact("/")),
    ("month", _exact("/month/")),
    ("detailed", _within("/detailed/")),
    ("expenses", _within("/expenses/", excluding=LEDGER_ELSEWHERE)),
    ("incomes", _exact("/incomes/")),
    ("transactions", _exact("/transactions/")),
    ("savings", _within("/savings/", excluding=LEDGER_ELSEWHERE)),
    ("debts", _exact("/debts/")),
    ("books", _within("/books/")),
    ("drinks", _exact("/drinks/")),
    ("counts", _within("/counts/")),
    ("plans", _within("/plans/")),
    ("charts", _within("summary")),
    ("settings", _within("settings")),
)


def nav_active(request):
    return {
        "nav_active": frozenset(
            name for name, matches in NAV_RULES if matches(request.path)
        )
    }


def csp_nonce(request):
    return {"csp_nonce": getattr(request, "_csp_nonce", "")}
