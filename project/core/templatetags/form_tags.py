from django import template
from django.forms import CheckboxInput, Select, SelectMultiple

register = template.Library()

@register.filter(name='is_select')
def is_select(field):
    # Checks for both standard dropdowns and multi-selects
    return isinstance(field.field.widget, (Select, SelectMultiple))


@register.filter(name='is_checkbox')
def is_checkbox(field):
    return isinstance(field.field.widget, CheckboxInput)