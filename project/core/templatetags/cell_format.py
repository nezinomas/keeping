from django import template

register = template.Library()


@register.filter
def negative(value):
    _value = ''

    try:
        value = float(value)
    except:
        return _value

    if value < 0:
        _value = 'table-danger'

    return _value


@register.filter
def positive(value):
    _value = ''

    try:
        value = float(value)
    except:
        return _value

    if value >= 0:
        _value = 'table-success'

    return _value


@register.filter
def positive_negative(value):
    _value = ''

    try:
        value = float(value.replace('.', '').replace(',', '.'))
    except:
        return _value

    if value >= 0:
        _value = 'table-success'
    else:
        _value = 'table-danger'

    return _value
