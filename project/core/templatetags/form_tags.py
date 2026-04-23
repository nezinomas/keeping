from django import template
from django.forms import Select, SelectMultiple

register = template.Library()

@register.filter(name='is_select')
def is_select(field):
    # Checks for both standard dropdowns and multi-selects
    return isinstance(field.field.widget, (Select, SelectMultiple))