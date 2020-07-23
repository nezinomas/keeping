from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.mixins.form_mixin import FormForUserMixin
from .models import Pension, PensionType


class PensionForm(forms.ModelForm):
    class Meta:
        model = Pension
        fields = ['date', 'price', 'fee', 'remark', 'pension_type']

        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'pension_type', 'price', 'fee', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['date'].initial = datetime.now()

        # overwrite ForeignKey saving_type queryset
        self.fields['pension_type'].queryset = PensionType.objects.items()

        self.fields['date'].label = 'Data'
        self.fields['price'].label = 'Suma'
        self.fields['fee'].label = 'Mokestis'
        self.fields['remark'].label = 'Pastaba'
        self.fields['pension_type'].label = 'Fondas'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        fee = cleaned_data.get('fee')

        if not price and not fee:
            _msg = 'Laukeliai `Suma` ir `Mokestis` abu negali būti tušti.'

            self.add_error('price', _msg)
            self.add_error('fee', _msg)

        return

class PensionTypeForm(FormForUserMixin, forms.ModelForm):
    class Meta:
        model = PensionType
        fields = ['title']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].label = 'Fondo pavadinimas'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
