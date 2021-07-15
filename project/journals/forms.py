import json
from json.decoder import JSONDecodeError

from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..expenses.models import ExpenseType


class UnnecessaryForm(forms.Form):
    choices = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    savings = forms.BooleanField(required=False)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['choices'].queryset = ExpenseType.objects.items()

        user = utils.get_user()
        checked_expenses = []

        try:
            checked_expenses = json.loads(user.journal.unnecessary_expenses)
        except (JSONDecodeError, TypeError):
            pass

        self.initial['choices'] = checked_expenses
        self.initial['savings'] = user.journal.unnecessary_savings

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

        self.fields['savings'].widget.attrs['class'] = " form-check-input"
        self.fields['savings'].label = "Taupymas"

        self.fields['choices'].label = False

        self.helper.form_show_labels = True


    def save(self):
        journal = utils.get_user().journal

        choices = None
        if self.cleaned_data.get("choices"):
            choices = list(self.cleaned_data["choices"].values_list("pk", flat=True))
            choices = json.dumps(choices)

        journal.unnecessary_expenses = choices
        journal.unnecessary_savings = self.cleaned_data.get('savings')

        journal.save()
