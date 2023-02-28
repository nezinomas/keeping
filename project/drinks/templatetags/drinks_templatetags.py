from django import template

from ..lib.drinks_options import DrinksOptions

register = template.Library()


@register.filter
def convert(stdav: float, drink_type: str):
    node = DrinksOptions().get_node(drink_type)
    return stdav / node.get("stdav", 1)
