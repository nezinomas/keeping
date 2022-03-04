from django import template

register = template.Library()


@register.inclusion_tag('bookkeeping/includes/detailed_table.html',
                        takes_context=True)
def detailed_table(context, name, items, total_row, total_col, total):
    return {
        'months': context['months'],
        'month_names': context['month_names'],
        'name': name,
        'items': items,
        'total_row': total_row,
        'total_col': total_col,
        'total': total,
    }


@register.inclusion_tag('bookkeeping/includes/info_table.html')
def info_table(_dict):
    rtn = {
        'title': None,
        'data': None,
        'highlight': None,
    }
    for k in rtn:
        try:
            rtn[k] = _dict.get(k)
        except AttributeError:
            continue

    return rtn


@register.inclusion_tag('bookkeeping/includes/worth_table.html')
def funds_table(_dict, _type=None):
    rtn = {
        'title': None,
        'items': None,
        'total_row': None,
        'percentage_from_incomes': None,
        'profit_incomes_proc': None,
        'profit_invested_proc': None,
    }

    for k in rtn:
        try:
            rtn[k] = _dict.get(k)
        except AttributeError:
            continue

    rtn['type'] = _type

    return rtn
