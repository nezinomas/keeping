from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import floatformat

register = template.Library()


@register.filter
def decimalformat(value):
    _value = '-'

    try:
        _value = float(value)
    except:
        return _value

    if value:
        _value = floatformat(value, 2)
        _value = intcomma(_value)

    return _value
