from django.utils.translation import gettext as _
from crispy_forms.helper import FormHelper
from django import forms

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..expenses.models import ExpenseType
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


class SummaryExpensesForm(forms.Form):
    types = forms.MultipleChoiceField(
        required=False
    )
    names = forms.CharField(
        widget=forms.HiddenInput(),
        disabled=True,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        for _type in ExpenseType.objects.items():
            choices.append((_type.id, _type.title))

            for _name in _type.expensename_set.all():
                choices.append(
                    (f'{_type.id}:{_name.id}', _name.title))

        self.fields['types'].choices = choices
        self.fields['types'].label = None

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def clean(self):
        cleaned_data = super().clean()
        _types = cleaned_data.get('types')
        _names = cleaned_data.get('names')

        if not _types and not _names:
            raise forms.ValidationError(
                _('At least one category needs to be selected.')
            )
        return cleaned_data
