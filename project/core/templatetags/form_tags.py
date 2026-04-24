from django import template
from django.forms import CheckboxInput, Select, SelectMultiple, FileInput, ClearableFileInput

register = template.Library()

@register.filter(name='is_select')
def is_select(field):
    # Checks for both standard dropdowns and multi-selects
    return isinstance(field.field.widget, (Select, SelectMultiple))


@register.filter(name='is_checkbox')
def is_checkbox(field):
    return isinstance(field.field.widget, CheckboxInput)


@register.filter(name='is_file')
def is_file(field):
    # Checks for standard file inputs and Django's default clearable inputs
    return isinstance(field.field.widget, (FileInput, ClearableFileInput))