from django.template.defaultfilters import floatformat

from .convert_price import int_cents_to_float

NOTHING = "–"


def amount(cents: int) -> str:
    return floatformat(int_cents_to_float(cents), "0g") if cents else NOTHING


def share(cents: int, total: int) -> str:
    if not cents or not total:
        return NOTHING

    if cents == total:
        return "100%"

    percent = cents / total * 100

    if percent < 0.5:
        return "< 1%"

    if percent >= 99.5:
        return "> 99%"

    return f"{floatformat(percent, '0')}%"
