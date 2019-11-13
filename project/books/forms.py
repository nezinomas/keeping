from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['started', 'ended', 'author', 'title']

        widgets = {
            'started': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ).start_of('event days'),
            'ended': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ).end_of('event days'),
        }

    field_order = ['started', 'ended', 'author', 'title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['started'].initial = datetime.now()

        self.fields['started'].label = 'Pradėta skaityti'
        self.fields['ended'].label = 'Pabaigta skaityti'
        self.fields['title'].label = 'Pavadinimas'
        self.fields['author'].label = 'Autorius'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
