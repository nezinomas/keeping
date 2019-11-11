from django import template

register = template.Library()


@register.inclusion_tag('bookkeeping/includes/savings_worth_table.html', takes_context=True)
def savings_worth_table(context,
                        items,
                        total_row,
                        label=None,
                        percentage_from_incomes=None):

    return {
        'items': items,
        'total_row': total_row,
        'label': label,
        'percentage_from_incomes': context.get('percentage_from_incomes'),
    }
