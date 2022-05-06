from typing import Any
from django import template

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
def negative(value):
    try:
        value = float(value)
    except ValueError:
        return str()

    if value < 0:
        return 'table-danger'

    return str()


@register.filter
def positive(value):
    try:
        value = float(value)
    except ValueError:
        return str()

    if value >= 0:
        return 'table-success'

    return str()


@register.filter
def positive_negative(value):
    try:
        value = _to_float(value)
    except ValueError:
        return str()

    if value >= 0:
        return 'table-success'

    return 'table-danger'


@register.filter
def compare(value: str, args: str) -> str:
    try:
        _value = _to_float(value)
        _compare = _to_float(args)
    except (TypeError, ValueError):
        return str()

    if _value >= _compare:
        return 'table-success'

    return 'table-danger'
