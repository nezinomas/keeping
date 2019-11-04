from typing import Any
from decimal import Decimal
from django import template

register = template.Library()


def _to_float(_str: Any) -> float:
    if type(_str) == float or type(_str) == int or type(_str) == Decimal:
        return float(_str)
    else:
        return float(_str.replace('.', '').replace(',', '.'))


@register.filter
def negative(value):
    _value = ''

    try:
        value = float(value)
    except:
        return _value

    if value < 0:
        _value = 'table-danger'

    return _value


@register.filter
def positive(value):
    _value = ''

    try:
        value = float(value)
    except:
        return _value

    if value >= 0:
        _value = 'table-success'

    return _value


@register.filter
def positive_negative(value):
    _value = ''

    try:
        value = _to_float(value)
    except:
        return _value

    if value >= 0:
        _value = 'table-success'
    else:
        _value = 'table-danger'

    return _value


@register.filter
def compare(value: str, args: str) -> str:
    _value = ''

    try:
        value = _to_float(value)
        compare = _to_float(args)
    except Exception as ex:
        return _value

    if value >= compare:
        _value = 'table-success'
    else:
        _value = 'table-danger'

    return _value
