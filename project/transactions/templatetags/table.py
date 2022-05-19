from django import template

register = template.Library()


@register.inclusion_tag(
    'transactions/includes/table.html',
    takes_context=True
)
def table(context, url_update, url_delete, fee=False):
    try:
        year = context['request'].user.year
    except Exception as ex:
        year = None

    return {
        'url_update': url_update,
        'url_delete': url_delete,
        'object_list': context['object_list'],
        'year': year,
        'fee': fee
    }
