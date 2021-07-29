from django import template
from django.utils.safestring import mark_safe

from ...core.lib.transalation import month_names

register = template.Library()


@register.simple_tag
def months():
    return mark_safe(list(month_names().values()))
