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
