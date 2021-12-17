from django import template

from ...core.lib.transalation import month_names

register = template.Library()


@register.inclusion_tag('plans/includes/generic_list.html')
def generic_list(year, items, type=None, update=None, delete=None):
    return {
        'year': year,
        'items': items,
        'type': type,
        'update': update,
        'delete': delete,
        'months': list(month_names().values()),
    }
