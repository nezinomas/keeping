from django import template

register = template.Library()


@register.inclusion_tag('bookkeeping/includes/savings_worth_table.html')
def savings_worth_table(items, total_row, label=None):
    return {
        'items': items,
        'total_row': total_row,
        'label': label
    }
