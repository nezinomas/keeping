from django import template
from django.forms import (
    CheckboxInput,
    ClearableFileInput,
    FileInput,
    Select,
    SelectMultiple,
)

from ..lib.form_widgets import DatePickerWidget, YearPickerWidget

register = template.Library()


@register.filter(name="is_select")
def is_select(field):
    return isinstance(field.field.widget, (Select, SelectMultiple))


@register.filter(name="is_checkbox")
def is_checkbox(field):
    return isinstance(field.field.widget, CheckboxInput)


@register.filter(name="is_file")
def is_file(field):
    return isinstance(field.field.widget, (FileInput, ClearableFileInput))


@register.filter(name="has_date_picker")
def has_date_picker(form):
    return _has_widget(form, DatePickerWidget)


@register.filter(name="has_year_picker")
def has_year_picker(form):
    return _has_widget(form, YearPickerWidget)


def _has_widget(form, widget_class):
    # `{% if %}` hands a missing `form` to the filter as None
    if form is None:
        return False

    return any(isinstance(field.field.widget, widget_class) for field in form)
