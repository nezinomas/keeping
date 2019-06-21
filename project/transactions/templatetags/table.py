from django import template

register = template.Library()


@register.inclusion_tag(
    'transactions/includes/table.html',
    takes_context=True
)
def table(context, url_name):
    try:
        year = context['request'].user.profile.year
    except:
        year = None

    return {
        'url_name': url_name,
        'items': context['items'],
        'year': year,
    }
