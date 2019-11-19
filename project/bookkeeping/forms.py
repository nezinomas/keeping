from crispy_forms.helper import FormHelper
from django import forms

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..pensions.models import PensionType
from ..savings.models import SavingType
from .models import AccountWorth, PensionWorth, SavingWorth


class SavingWorthForm(forms.ModelForm):
    class Meta:
        model = SavingWorth
        fields = ['saving_type', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form initial values
        self.fields['price'].initial = '0'

        # overwrite FK
        self.fields['saving_type'].queryset = SavingType.objects.items()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class AccountWorthForm(forms.ModelForm):
    class Meta:
        model = AccountWorth
        fields = ['account', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form initial values
        self.fields['price'].initial = '0'

        # overwrite FK
        self.fields['account'].queryset = Account.objects.items()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class PensionWorthForm(forms.ModelForm):
    class Meta:
        model = PensionWorth
        fields = ['pension_type', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['price'].initial = '0'

        # overwrite FK
        self.fields['pension_type'].queryset = PensionType.objects.items()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
