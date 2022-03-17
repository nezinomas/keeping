from django import template
from django.utils.safestring import mark_safe

from ...core.lib.translation import weekday_names

register = template.Library()


@register.simple_tag
def first_letters():
    arr = [x[0] for x in list(weekday_names().values())]

    return mark_safe(arr)
