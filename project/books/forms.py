from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib.date import set_year_for_form
from ..core.mixins.form_mixin import FormForUserMixin
from .models import Book


class BookForm(FormForUserMixin, forms.ModelForm):
    class Meta:
        model = Book
        fields = ['started', 'ended', 'author', 'title', 'remark']

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

    field_order = ['started', 'ended', 'author', 'title', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # inital values
        self.fields['started'].initial = set_year_for_form()

        self.fields['started'].label = 'Pradėta skaityti'
        self.fields['ended'].label = 'Pabaigta skaityti'
        self.fields['title'].label = 'Pavadinimas'
        self.fields['author'].label = 'Autorius'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
