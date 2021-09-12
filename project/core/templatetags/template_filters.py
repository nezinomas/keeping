from django import template
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key, 0.0)


@register.filter
def cellformat(value, default='-'):
    if not default:
        default = '-'

    if value is None:
        return default

    try:
        _value = float(value)
    except:
        return value

    # first round _value
    _value = round(_value, 2)

    if _value == 0.0:
        _value = default
    else:
        _value = floatformat(_value, 2)

    return _value


@register.filter
def weekend(value, css_class):
    if int(value) in (0, 6):
        return css_class

    return ''
