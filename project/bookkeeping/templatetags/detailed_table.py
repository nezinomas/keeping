from django import template

register = template.Library()


@register.inclusion_tag('bookkeeping/includes/detailed_table.html',
                        takes_context=True)
def detailed_table(context, name, items, total):
    return {
        'months': context['months'],
        'name': name,
        'items': items,
        'total': total,
    }
