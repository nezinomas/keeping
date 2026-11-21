from datetime import date

from django.template.defaultfilters import floatformat

from .convert_price import int_cents_to_float

NOTHING = "–"


def amount(cents: int, places: str = "0g") -> str:
    return floatformat(int_cents_to_float(cents), places) if cents else NOTHING


def percent(figure: float) -> str:
    """A percent in one decimal, without its "%"."""
    return floatformat(figure, "1g")


def day(when: date) -> str:
    return f"{when:%Y-%m-%d}"


def share(cents: int, total: int) -> str:
    if not cents or not total:
        return NOTHING

    if cents == total:
        return "100%"

    part = cents / total * 100

    if part < 0.5:
        return "< 1%"

    if part >= 99.5:
        return "> 99%"

    return f"{floatformat(part, '0')}%"
