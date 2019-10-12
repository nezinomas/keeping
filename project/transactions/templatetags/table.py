from django import template

register = template.Library()


@register.inclusion_tag(
    'transactions/includes/table.html',
    takes_context=True
)
def table(context, url_name, fees=False):
    try:
        year = context['request'].user.profile.year
    except:
        year = 'XXXX'

    return {
        'url_name': url_name,
        'items': context['items'],
        'year': year,
        'fees': fees
    }
