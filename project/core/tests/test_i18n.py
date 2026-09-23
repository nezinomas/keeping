from django import forms
from django.contrib.auth.models import Group


def test_blank_choice_label_is_translated():
    field = forms.ModelChoiceField(queryset=Group.objects.none())

    assert str(field.empty_label) == "- Pasirinkti -"
