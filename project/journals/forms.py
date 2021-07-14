import json
from json.decoder import JSONDecodeError

from crispy_forms.helper import FormHelper
from django import forms

from ..core.helpers.helper_forms import set_field_properties
from ..core.lib import utils
from ..expenses.models import ExpenseType


class NotUseForm(forms.Form):
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
            checked_expenses = json.loads(user.journal.not_use_expenses)
        except (JSONDecodeError, TypeError):
            pass

        self.initial['choices'] = checked_expenses
        self.initial['savings'] = user.journal.not_use_savings

        self.helper = FormHelper()
        set_field_properties(self, self.helper)

    def save(self):
        journal = utils.get_user().journal

        choices = None
        if self.cleaned_data.get("choices"):
            choices = list(self.cleaned_data["choices"].values_list("pk", flat=True))
            choices = json.dumps(choices)

        journal.not_use_expenses = choices
        journal.not_use_savings = self.cleaned_data.get('savings')

        journal.save()
