from django import template

register = template.Library()


@register.inclusion_tag(
    'transactions/includes/table.html',
    takes_context=True
)
def table(context, url_update):
    year = context['request'].user.profile.year
    return {
        'url_update': url_update,
        'items': context['items'],
        'year': year,
    }
