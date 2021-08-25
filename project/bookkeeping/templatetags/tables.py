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
    try:
        title = _dict.get('title')
        data = _dict.get('data')
        highlight = _dict.get('highlight')
    except AttributeError:
        return {}

    return {
        'title': title,
        'data': data,
        'highlight': highlight,
    }
