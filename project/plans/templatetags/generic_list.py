from django import template

from ...core.lib.transalation import month_names

register = template.Library()


@register.inclusion_tag('plans/includes/generic_list.html')
def generic_list(items, url_update, year, type=None, url_delete=None):
    return {
        'items': items,
        'url_update': url_update,
        'year': year,
        'type': type,
        'url_delete': url_delete,
        'months': list(month_names().values()),
    }
