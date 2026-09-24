from django import forms
from django.contrib.auth.models import Group
from django.template.loader import render_to_string


def test_blank_choice_label_is_translated():
    field = forms.ModelChoiceField(queryset=Group.objects.none())

    assert str(field.empty_label) == "- Pasirinkti -"


def test_dropdown_blank_option_matches_form_blank_choice():
    actual = render_to_string("core/dropdown.html", {"object_list": []})

    assert '<option value="">- Pasirinkti -</option>' in actual
