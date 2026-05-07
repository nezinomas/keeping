from django import template

from ..lib.drinks_options import DrinksOptions

register = template.Library()


@register.filter
def convert_to_quantity(stdav: float, drink_type: str):
    return stdav * DrinksOptions(drink_type).ratio


@register.filter
def convert_to_ml(stdav: float, drink_type: str):
    return DrinksOptions(drink_type).stdav_to_ml(stdav)
