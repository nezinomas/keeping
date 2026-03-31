from django import template

from ..lib.drinks_options import DrinksOptions

register = template.Library()


@register.filter
def convert_to_quantity(stdav: float, drink_type: str):
    node = DrinksOptions(drink_type).get_node()
    return stdav / node.get("stdav", 1)


@register.filter
def convert_to_ml(stdav: float, drink_type: str):
    return DrinksOptions(drink_type).stdav_to_ml(stdav, drink_type)