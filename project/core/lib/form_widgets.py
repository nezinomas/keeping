from django import forms
from django.utils.translation import gettext_lazy as _


class DatePickerWidget(forms.DateInput):
    def __init__(self, attrs=None):
        default_attrs = {
            "class": "date-picker",
            "placeholder": _("Select a date"),
        }
        if attrs:
            default_attrs |= attrs
        super().__init__(attrs=default_attrs, format="%Y-%m-%d")


class YearPickerWidget(forms.TextInput):
    def __init__(self, attrs=None):
        default_attrs = {
            "class": "year-picker",
            "placeholder": _("Select a year"),
        }
        if attrs:
            default_attrs |= attrs
        super().__init__(attrs=default_attrs)


class DecimalCommaWidget(forms.TextInput):
    # text because a number input drops the comma instead of rejecting it, and
    # keyup because x-model binds on input and writes its value back over this
    def __init__(self, attrs=None):
        default_attrs = {
            "inputmode": "decimal",
            "@keyup": "$el.value = $el.value.replace(',', '.')"
            r".replace(/[^0-9.]/g, '').replace(/^(\d*\.?\d*).*/, '$1')",
        }
        if attrs:
            default_attrs |= attrs
        super().__init__(attrs=default_attrs)
