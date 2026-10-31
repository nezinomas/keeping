from django import template

from ..lib.translation import MONTH_ABBREVIATIONS

register = template.Library()


@register.simple_tag
def month_abbreviations():
    return MONTH_ABBREVIATIONS
