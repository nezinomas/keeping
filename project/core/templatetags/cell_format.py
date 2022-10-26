from typing import Any

from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


def _to_float(_str: Any) -> float:
    if isinstance(_str, str):
        _str = _str.replace('.', str())
        _str = _str.replace(',', '.')
    try:
        return float(_str)
    except ValueError:
        return float()


@register.filter
def cellformat(value, default: str = '-'):
    value = None if value == 'None' else value

    try:
        _value = float(value)
    except TypeError:
        return default
    except ValueError:
        return value

    # round value and convert to str
    _value = floatformat(_value, 2)

    return default if _value == '0,00' else _value


@register.filter
def negative(value):
    try:
        value = float(value)
    except ValueError:
        return str()

    return 'table-danger' if value < 0 else str()


@register.filter
def positive(value):
    try:
        value = float(value)
    except ValueError:
        return str()

    return 'table-success' if value >= 0 else str()


@register.filter
def positive_negative(value):
    try:
        value = _to_float(value)
    except ValueError:
        return str()

    return 'table-success' if value >= 0 else 'table-danger'


@register.filter
def compare(value: str, args: str) -> str:
    try:
        _value = _to_float(value)
        _compare = _to_float(args)
    except (TypeError, ValueError):
        return str()

    return 'table-success' if _value >= _compare else 'table-danger'
