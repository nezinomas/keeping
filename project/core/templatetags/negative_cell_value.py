from django import template

register = template.Library()


@register.filter
def negativecell(value):
    return_value = ''

    try:
        _value = float(value)
    except:
        return _value

    if _value < 0:
        return_value = 'table-danger'

    return return_value
