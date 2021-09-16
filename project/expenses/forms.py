from bootstrap_datepicker_plus import DatePickerInput, YearPickerInput
from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..accounts.models import Account
from ..core.helpers.helper_forms import ChainedDropDown, set_field_properties
from ..core.lib import utils
from ..core.lib.date import set_year_for_form
from .models import Expense, ExpenseName, ExpenseType


class ExpenseForm(forms.ModelForm):
    total_sum = forms.CharField(required=False)

    class Meta:
        model = Expense
        fields = ('date', 'price', 'quantity', 'expense_type',
                  'expense_name', 'remark', 'exception', 'account', 'attachment')

    field_order = [
        'date',
        'expense_type',
        'expense_name',
        'account',
        'total_sum',
        'quantity',
        'remark',
        'price',
        'attachment',
        'exception'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['date'].widget = DatePickerInput(
            options={
                "format": "YYYY-MM-DD",
                "locale": utils.get_user().journal.lang,
            })

        # inital values
        self.fields['date'].initial = set_year_for_form()
        self.fields['account'].initial = Account.objects.items().first()
        self.fields['price'].initial = '0.00'
        self.fields['expense_name'].queryset = Expense.objects.none()

        # overwrite ForeignKey expense_type queryset
        self.fields['expense_type'].queryset = ExpenseType.objects.items()
        self.fields['account'].queryset = Account.objects.items()

        # chained dropdown to select expense_names
        _id = ChainedDropDown(self, 'expense_type').parent_field_id
        if _id:
            year = utils.get_user().year
            self.fields['expense_name'].queryset = (
                ExpenseName.objects.parent(_id).year(year)
            )

        # form inputs settings
        self.fields['price'].widget.attrs = {'readonly': True, 'step': '0.01'}
        self.fields['remark'].widget.attrs['rows'] = 3

        # field translation
        self.fields['date'].label = _('Date')
        self.fields['price'].label = _('Full price')
        self.fields['quantity'].label = _('How many')
        self.fields['expense_type'].label = _('Expense type')
        self.fields['expense_name'].label = _('Expense name')
        self.fields['remark'].label = _('Remark')
        self.fields['exception'].label = _('Exception')
        self.fields['account'].label = _('Account')
        self.fields['total_sum'].label = _('Price')
        self.fields['attachment'].label = _('Attachment')

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['exception'].widget.attrs['class'] = " form-check-input"
        self.fields['attachment'].widget.attrs['class'] = 'form-control form-control-sm'


    def clean_exception(self):
        data = self.cleaned_data

        _exception = data.get('exception')
        _expense_type = data.get('expense_type')

        if _exception and _expense_type.necessary:
            msg = _("The %(title)s is 'Necessary', so it can't be marked as 'Exeption'") % {'title': _expense_type.title}
            raise forms.ValidationError(msg)

        return _exception

    def clean_attachment(self):
        image = self.cleaned_data.get('attachment', False)

        if image:
            if image.size > 4*1024*1024:
                raise ValidationError(_("Image file too large ( > 4Mb )"))

        return image

    def clean_date(self):
        dt = self.cleaned_data['date']

        if dt:
            year_user = utils.get_user().year
            year_instance = dt.year

            diff = 3
            if (year_user - year_instance) > diff:
                year_msg = year_user - diff
                self.add_error(
                    'date',
                    _('Year cannot be less than %(year)s') % (
                        {'year': year_msg})
                )

        return dt

class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ['journal', 'title', 'necessary']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # journal input
        self.fields['journal'].initial = utils.get_user().journal
        self.fields['journal'].disabled = True
        self.fields['journal'].widget = forms.HiddenInput()

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['title'].label = _('Title')
        self.fields['necessary'].label = _('Necessary')

        self.fields['necessary'].widget.attrs['class'] = " form-check-input necessary_check "


class ExpenseNameForm(forms.ModelForm):
    class Meta:
        model = ExpenseName
        fields = ['parent', 'title', 'valid_for']

        widgets = {
            'valid_for': YearPickerInput(format='%Y'),
        }

    field_order = ['parent', 'title', 'valid_for']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # overwrite ForeignKey parent queryset
        self.fields['parent'].queryset = ExpenseType.objects.items()

        # field labels
        self.fields['parent'].label = _('Expense type')
        self.fields['title'].label = _('Expense name')
        self.fields['valid_for'].label = _('Valid for')

        # crispy forms settings
        self.helper = FormHelper()
        set_field_properties(self, self.helper)
