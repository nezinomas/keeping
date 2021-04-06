from django import template

register = template.Library()


@register.inclusion_tag(
    'transactions/includes/table.html',
    takes_context=True
)
def table(context, url_update, url_delete, fees=False):
    try:
        year = context['request'].user.year
    except Exception as ex:
        year = None

    return {
        'url_update': url_update,
        'url_delete': url_delete,
        'items': context['items'],
        'year': year,
        'fees': fees
    }
