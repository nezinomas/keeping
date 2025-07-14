import contextlib
import json
from json.decoder import JSONDecodeError

from django import forms
from django.conf import settings
from django.utils.translation import gettext as _

from ..core.lib import utils
from ..expenses.models import ExpenseType


class UnnecessaryForm(forms.Form):
    choices = forms.ModelMultipleChoiceField(
        queryset=None, widget=forms.CheckboxSelectMultiple, required=False
    )
    savings = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["choices"].queryset = ExpenseType.objects.items()

        user = utils.get_user()
        checked_expenses = []

        with contextlib.suppress(JSONDecodeError, TypeError):
            checked_expenses = json.loads(user.journal.unnecessary_expenses)

        self.initial["choices"] = checked_expenses
        self.initial["savings"] = user.journal.unnecessary_savings

        self.fields["savings"].label = _("Savings")
        self.fields["choices"].label = False

    def save(self):
        journal = utils.get_user().journal

        choices = None
        if self.cleaned_data.get("choices"):
            choices = list(self.cleaned_data["choices"].values_list("pk", flat=True))
            choices = json.dumps(choices)

        journal.unnecessary_expenses = choices
        journal.unnecessary_savings = self.cleaned_data.get("savings")

        journal.save()


class SettingsForm(forms.Form):
    lang = forms.ChoiceField(choices=settings.LANGUAGES)
    title = forms.CharField(required=True, min_length=3, max_length=254)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        journal = utils.get_user().journal

        self.fields["lang"].initial = journal.lang
        self.fields["title"].initial = journal.title

        self.fields["lang"].label = _("Journal language")
        self.fields["title"].label = _("Journal title")

    def save(self):
        journal = utils.get_user().journal

        if lang := self.cleaned_data.get("lang"):
            journal.lang = lang

        if title := self.cleaned_data.get("title"):
            journal.title = title

        journal.save()
