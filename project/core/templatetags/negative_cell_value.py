from django import template

register = template.Library()


@register.filter
def negativecell(value):
    _value = ''

    try:
        _value = float(value)
    except:
        return _value

    if value < 0:
        _value = 'table-danger'

    return _value
