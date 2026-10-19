import contextlib
import json
from json.decoder import JSONDecodeError

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from ..core.mixins.forms import UserTodayMixin
from ..expenses.services.model_services import ExpenseTypeModelService
from .models import Journal


def pks_json(choices):
    return json.dumps(list(choices.values_list("pk", flat=True)))


class UnnecessaryForm(UserTodayMixin, forms.Form):
    choices = forms.ModelMultipleChoiceField(
        queryset=None, widget=forms.CheckboxSelectMultiple, required=False
    )
    savings = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["choices"].queryset = ExpenseTypeModelService(self.user).objects

        checked_expenses = []

        with contextlib.suppress(JSONDecodeError, TypeError):
            checked_expenses = json.loads(self.user.journal.unnecessary_expenses)

        self.initial["choices"] = checked_expenses
        self.initial["savings"] = self.user.journal.unnecessary_savings

        self.fields["savings"].label = _("Savings")
        self.fields["choices"].label = False

    def clean_choices(self):
        choices = self.cleaned_data["choices"]

        column = Journal._meta.get_field("unnecessary_expenses")
        if len(pks_json(choices)) > column.max_length:
            raise ValidationError(_("Too many expense types selected."))

        return choices

    def save(self):
        journal = self.user.journal

        journal.unnecessary_expenses = pks_json(self.cleaned_data["choices"])
        journal.unnecessary_savings = self.cleaned_data["savings"]

        journal.save()


class SettingsForm(UserTodayMixin, forms.Form):
    lang = forms.ChoiceField(choices=settings.LANGUAGES)
    title = forms.CharField(validators=Journal._meta.get_field("title").validators)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        journal = self.user.journal

        self.fields["lang"].initial = journal.lang
        self.fields["title"].initial = journal.title

        self.fields["lang"].label = _("Journal language")
        self.fields["title"].label = _("Journal title")

    def save(self):
        journal = self.user.journal

        if lang := self.cleaned_data.get("lang"):
            journal.lang = lang

        if title := self.cleaned_data.get("title"):
            journal.title = title

        journal.save()
