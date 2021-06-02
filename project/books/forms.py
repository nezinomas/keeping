from bootstrap_datepicker_plus import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from .models import Book, BookTarget


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['user', 'started', 'ended', 'author', 'title', 'remark']

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

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        # inital values
        self.fields['started'].initial = set_year_for_form()

        self.fields['started'].label = 'Pradėta skaityti'
        self.fields['ended'].label = 'Pabaigta skaityti'
        self.fields['title'].label = 'Pavadinimas'
        self.fields['author'].label = 'Autorius'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)



class BookTargetForm(forms.ModelForm):
    class Meta:
        model = BookTarget
        fields = ['user', 'year', 'quantity']

        widgets = {
            'year': YearPickerInput(format='%Y'),
        }

    field_order = ['year', 'quantity']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

        # inital values
        self.fields['year'].initial = set_year_for_form()

        self.fields['year'].label = 'Metai'
        self.fields['quantity'].label = 'Kiekis ml'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean_year(self):
        year = self.cleaned_data['year']

        # if update
        if self.instance.pk:
            return year

        # if new record
        qs = BookTarget.objects.year(year)
        if qs.exists():
            raise forms.ValidationError(f'{year} metai jau turi tikslą.')

        return year
