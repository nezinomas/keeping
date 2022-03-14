from django import template

from ..lib.drinks_options import DrinksOptions

register = template.Library()


@register.filter
def convert(stdav: float, to: str):
    return stdav / DrinksOptions().ratios.get(to, {}).get('stdav', 1)
