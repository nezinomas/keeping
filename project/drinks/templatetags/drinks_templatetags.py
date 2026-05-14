from django import template

from ..lib.drinks_options import DrinkConverter

register = template.Library()


@register.filter
def convert_to_quantity(stdav: float, drink_type: str):
    return stdav * DrinkConverter(drink_type).ratio


@register.filter
def convert_to_ml(stdav: float, drink_type: str):
    return DrinkConverter(drink_type).stdav_to_ml(stdav)
