from django import template

from ..lib.convert_price import int_cents_to_float

register = template.Library()


@register.filter
def price(value):
    try:
        return int_cents_to_float(value)
    except TypeError:
        return value


@register.filter
def sub(a, b):
    try:
        return a - b
    except TypeError:
        return 0
