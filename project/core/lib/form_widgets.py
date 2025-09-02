from django import forms


class DatePickerWidget(forms.DateInput):
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'date-picker',
            'placeholder': 'Select a date',
        }
        if attrs:
            default_attrs |= attrs
        super().__init__(attrs=default_attrs, format='%Y-%m-%d')


class YearPickerWidget(forms.TextInput):
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'year-picker',
            'placeholder': 'Select a year',
        }
        if attrs:
            default_attrs |= attrs
        super().__init__(attrs=default_attrs)