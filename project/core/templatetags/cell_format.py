from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def cellformat(value, default: str = "-"):
    if isinstance(value, str):
        try:
            value = float(value.replace(",", "."))
        except ValueError:
            return default

    if value is None or round(value, 2) == 0:
        return default

    return floatformat(value, "2g")


@register.filter
def css_class_if_none(value, default: str = "dash"):
    value = None if value == "None" else value

    return "" if value else default


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
