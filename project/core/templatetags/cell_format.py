from django import template
from django.template.defaultfilters import floatformat

from ..lib.money_cells import rounds_to_zero

register = template.Library()


@register.filter
def cellformat(value, default: str = "-"):
    if isinstance(value, str):
        try:
            value = float(value.replace(",", "."))
        except ValueError:
            return default

    if value is None or rounds_to_zero(value):
        return default

    return floatformat(value, "2g")


@register.filter
def cell_state(value):
    state = "empty"
    if value:
        state = ""

    return state


@register.filter
def sign(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return ""

    state = "gain"
    if value < 0:
        state = "loss"

    return state
