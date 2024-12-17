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
    try:
        return a - b
    except TypeError:
        return 0


@register.filter
def percent(a: int | float, b: int | float) -> float:
    try:
        return (b / a) * 100
    except (ZeroDivisionError, TypeError):
        return 0
