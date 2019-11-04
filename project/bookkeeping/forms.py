from crispy_forms.helper import FormHelper
from django import forms
from django.forms.models import modelformset_factory

from ..core.helpers.helper_forms import set_field_properties
from ..savings.models import SavingType
from .models import AccountWorth, SavingWorth, PensionWorth


class SavingWorthForm(forms.ModelForm):
    class Meta:
        model = SavingWorth
        fields = ['saving_type', 'price']

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['saving_type'].queryset = SavingType.objects.items(year)

        self.fields['price'].initial = '0'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class AccountWorthForm(forms.ModelForm):
    class Meta:
        model = AccountWorth
        fields = ['account', 'price']

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['price'].initial = '0'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class PensionWorthForm(forms.ModelForm):
    class Meta:
        model = PensionWorth
        fields = ['pension_type', 'price']

    def __init__(self, year=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['price'].initial = '0'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
