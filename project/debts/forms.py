from django.core.exceptions import ValidationError
from bootstrap_datepicker_plus import DatePickerInput
from crispy_forms.helper import FormHelper
from django import forms

from ..accounts.models import Account
from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from . import models


class BorrowForm(forms.ModelForm):
    class Meta:
        model = models.Borrow
        fields = ['user', 'date', 'name', 'price', 'closed', 'account', 'remark']

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

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

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

        self.fields['closed'].widget.attrs['class'] = " form-check-input"

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        closed = cleaned_data.get('closed')

        if not closed:
            if name == self.instance.name:
                return

            qs = models.Borrow.objects.items().filter(name=name)
            if qs.exists():
                self.add_error('name', 'Skolininko vardas turi būti unikalus.')

        return


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
        self.fields['borrow'].queryset = models.Borrow.objects.items().filter(closed=False)
        self.fields['account'].queryset = Account.objects.items()

        # fields labels
        self.fields['account'].label = 'Sąskaita'
        self.fields['borrow'].label = 'Skolininkas'
        self.fields['price'].label = 'Suma'
        self.fields['remark'].label = 'Pastaba'

        self.helper = FormHelper()
        set_field_properties(self, self.helper)


    def clean_price(self):
        price = self.cleaned_data['price']
        borrow = self.cleaned_data.get('borrow')

        if borrow:
            obj = models.Borrow.objects.get(pk=borrow.pk)

            if price > obj.returned:
                raise ValidationError("Gražinama suma yra didesnė nei skola!")

        return price


class LentForm(forms.ModelForm):
    class Meta:
        model = models.Lent
        fields = ['user', 'date', 'name', 'price', 'closed', 'account', 'remark']

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

        # user input
        self.fields['user'].initial = utils.get_user()
        self.fields['user'].disabled = True
        self.fields['user'].widget = forms.HiddenInput()

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

        self.fields['closed'].widget.attrs['class'] = " form-check-input"

    def clean(self):
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        closed = cleaned_data.get('closed')

        if not closed:
            if name == self.instance.name:
                return

            qs = models.Lent.objects.items().filter(name=name)
            if qs.exists():
                self.add_error('name', 'Skolintojo vardas turi būti unikalus.')

        return


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
        self.fields['lent'].queryset = models.Lent.objects.items().filter(closed=False)
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

    def clean_price(self):
        price = self.cleaned_data['price']
        lent = self.cleaned_data.get('lent')

        if lent:
            obj = models.Lent.objects.get(pk=lent.pk)

            if price > obj.returned:
                raise ValidationError("Gražinama suma yra didesnė nei skola!")

        return price
