from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def cellformat(value, default: str = "-"):
    value = None if value == "None" else value

    if isinstance(value, str):
        value = value.replace(",", ".")

    try:
        _value = float(value)
    except TypeError:
        return default
    except ValueError:
        return value

    return floatformat(_value, "2g") if round(_value, 2) else default


@register.filter
def css_class_if_none(value, default: str = "dash"):
    value = None if value == "None" else value

    return "" if value else default


@register.filter
def negative(value):
    try:
        value = float(value)
    except ValueError:
        return str()

    return "table-danger" if value < 0 else str()


@register.filter
def positive(value):
    try:
        value = float(value)
    except ValueError:
        return str()

    return "table-success" if value >= 0 else str()


@register.filter
def positive_negative(value):
    try:
        value = float(value)
    except ValueError:
        return str()
    return "table-success" if value >= 0 else "table-danger"


@register.filter
def compare(value: str, args: str) -> str:
    try:
        _value = float(value)
        _compare = float(args)
    except (TypeError, ValueError):
        return str()

    return "table-success" if _value >= _compare else "table-danger"