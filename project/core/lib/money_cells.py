from django.template.defaultfilters import floatformat

from .convert_price import int_cents_to_float

NOTHING = "–"


def amount(cents: int) -> str:
    return floatformat(int_cents_to_float(cents), "0g") if cents else NOTHING


def share(cents: int, total: int) -> str:
    return f"{floatformat(cents / total * 100, '0')}%" if cents and total else NOTHING
