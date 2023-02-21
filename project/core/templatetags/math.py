from django import template

register = template.Library()


@register.filter
def price(value: int) -> float:
    return value / 100
