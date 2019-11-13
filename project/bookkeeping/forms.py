from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib.utils import get_user
from ..savings.models import SavingType
from .models import AccountWorth, PensionWorth, SavingWorth


class SavingWorthForm(forms.ModelForm):
    class Meta:
        model = SavingWorth
        fields = ['saving_type', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        year = get_user().year

        self.fields['saving_type'].queryset = SavingType.objects.items(year)

        self.fields['price'].initial = '0'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class AccountWorthForm(forms.ModelForm):
    class Meta:
        model = AccountWorth
        fields = ['account', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['price'].initial = '0'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class PensionWorthForm(forms.ModelForm):
    class Meta:
        model = PensionWorth
        fields = ['pension_type', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['price'].initial = '0'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
