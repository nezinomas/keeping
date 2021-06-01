from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib.date import set_year_for_form
from ..core.mixins.form_mixin import FormForUserMixin
from . import models


class BorrowForm(FormForUserMixin, forms.ModelForm):
    class Meta:
        model = models.Borrow
        fields = ['date', 'name', 'price', 'closed', 'account', 'remark']

    field_order = ['date', 'name', 'price', 'account', 'remark', 'closed']

    widgets = {
        'date': DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": "lt",
            }
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['account'].initial = Account.objects.items().first()
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['account'].queryset = Account.objects.items()

        # fields labels
        self.fields['date'].label = 'Data'
        self.fields['name'].label = 'Skolininkas'
        self.fields['account'].label = 'Sąskaita'
        self.fields['price'].label = 'Suma'
        self.fields['remark'].label = 'Pastaba'
        self.fields['closed'].label = 'Padengta'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class BorrowReturnForm(forms.ModelForm):
    class Meta:
        model = models.BorrowReturn
        fields = ['price', 'remark', 'account', 'borrow']

    field_order = ['borrow', 'account', 'price', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['account'].initial = Account.objects.items().first()

        # overwrite ForeignKey expense_type queryset
        self.fields['account'].queryset = Account.objects.items()

        # fields labels
        self.fields['account'].label = 'Sąskaita'
        self.fields['borrow'].label = 'Skolininkas'
        self.fields['price'].label = 'Suma'
        self.fields['remark'].label = 'Pastaba'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

class LentForm(FormForUserMixin, forms.ModelForm):
    class Meta:
        model = models.Lent
        fields = ['date', 'name', 'price', 'closed', 'account', 'remark']

    field_order = ['date', 'name', 'price', 'account', 'remark', 'closed']

    widgets = {
        'date': DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": "lt",
            }
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['account'].initial = Account.objects.items().first()
        self.fields['date'].initial = set_year_for_form()

        # overwrite ForeignKey expense_type queryset
        self.fields['account'].queryset = Account.objects.items()

        # fields labels
        self.fields['date'].label = 'Data'
        self.fields['name'].label = 'Skolintojas'
        self.fields['account'].label = 'Sąskaita'
        self.fields['price'].label = 'Suma'
        self.fields['remark'].label = 'Pastaba'
        self.fields['closed'].label = 'Padengta'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


class LentReturnForm(forms.ModelForm):
    class Meta:
        model = models.LentReturn
        fields = ['price', 'remark', 'account', 'lent']

    field_order = ['lent', 'account', 'price', 'remark']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # form inputs settings
        self.fields['remark'].widget.attrs['rows'] = 3

        # inital values
        self.fields['account'].initial = Account.objects.items().first()

        # overwrite ForeignKey expense_type queryset
        self.fields['account'].queryset = Account.objects.items()

        # fields labels
        self.fields['account'].label = 'Sąskaita'
        self.fields['lent'].label = 'Skolinintojas'
        self.fields['price'].label = 'Suma'
        self.fields['remark'].label = 'Pastaba'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)
