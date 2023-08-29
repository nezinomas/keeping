from django import template

register = template.Library()


@register.filter
def price(value: int) -> float:
    try:
        return value / 100
    except TypeError:
        return value


@register.filter
def sub(a: int, b: int) -> int:
    return a - b


@register.filter
def percent(a: int|float, b: int|float) -> float:
    try:
        return (100 * b) / a
    except ZeroDivisionError:
        return 0
