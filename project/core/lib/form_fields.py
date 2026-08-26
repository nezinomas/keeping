from django import forms

from .form_widgets import DecimalCommaWidget


class CommaFloatField(forms.FloatField):
    # a Lithuanian keyboard sends the decimal separator as a comma, verbatim
    widget = DecimalCommaWidget

    def to_python(self, value):
        if isinstance(value, str):
            value = value.strip().replace(",", ".")

        return super().to_python(value)
