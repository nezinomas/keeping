from django import template

register = template.Library()


@register.inclusion_tag('bookkeeping/includes/savings_worth_table.html')
def savings_worth_table(items, totals, label=None):
    return {
        'items': items,
        'totals': totals,
        'label': label
    }
