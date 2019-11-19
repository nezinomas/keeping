from datetime import datetime

from bootstrap_datepicker_plus import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.mixins.form_mixin import FormMixin
from .models import Saving, SavingType


class SavingTypeForm(FormMixin, forms.ModelForm):
    class Meta:
        model = SavingType
        fields = ['title', 'closed']

        widgets = {
            'closed': YearPickerInput(
                options={
                    "format": "YYYY",
                    "locale": "lt",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['title'].label = 'Fondas'
        self.fields['closed'].label = 'Uždaryta'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class SavingForm(forms.ModelForm):
    class Meta:
        model = Saving
        fields = ['date', 'price', 'fee', 'remark', 'saving_type', 'account']

        widgets = {
            'date': DatePickerInput(
                options={
                    "format": "YYYY-MM-DD",
                    "locale": "lt",
                }
            ),
        }

    field_order = ['date', 'saving_type', 'account', 'price', 'fee', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['price'].widget.attrs = {'step': '0.01'}
        self.fields['fee'].widget.attrs = {'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['account'].initial = Account.objects.items().first()
        self.fields['date'].initial = datetime.now()

        # overwrite ForeignKey saving_type and account queryset
        year = utils.get_user().year
        self.fields['saving_type'].queryset = SavingType.objects.items(year)
        self.fields['account'].queryset = Account.objects.items()

        self.fields['date'].label = 'Data'
        self.fields['account'].label = 'Iš sąskaitos'
        self.fields['price'].label = 'Suma'
        self.fields['fee'].label = 'Mokesčiai'
        self.fields['remark'].label = 'Pastaba'
        self.fields['saving_type'].label = 'Fondas'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
