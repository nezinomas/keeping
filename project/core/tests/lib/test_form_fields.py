import pytest
from django import forms

from ....accounts.models import Account
from ....accounts.tests.factories import AccountFactory
from ...lib.form_fields import CommaFloatField, PreloadedModelChoiceField
from ...lib.form_widgets import DecimalCommaWidget

pytestmark = pytest.mark.django_db


class Form(forms.Form):
    price = CommaFloatField()


class PreloadedForm(forms.Form):
    account = PreloadedModelChoiceField(queryset=Account.objects.none(), required=False)


def test_default_widget_is_decimal_comma():
    assert isinstance(Form().fields["price"].widget, DecimalCommaWidget)


def test_renders_a_decimal_keypad_for_a_phone():
    assert 'inputmode="decimal"' in str(Form()["price"])


def test_renders_as_text_input_with_a_dot():
    assert 'type="text"' in str(Form(initial={"price": 12.1})["price"])
    assert 'value="12.1"' in str(Form(initial={"price": 12.1})["price"])


@pytest.mark.parametrize(
    "value, expected",
    [
        ("12,1", 12.1),
        ("12.1", 12.1),
        ("12,10", 12.1),
        (" 12,1 ", 12.1),
        (12.1, 12.1),
    ],
)
def test_accepts_a_decimal_comma(value, expected):
    form = Form(data={"price": value})

    assert form.is_valid(), form.errors
    assert form.cleaned_data["price"] == expected


def test_rejects_a_non_number():
    assert not Form(data={"price": "abc"}).is_valid()


# ----------------------------------------------------------------------------
#                                                    PreloadedModelChoiceField
# ----------------------------------------------------------------------------
def test_preloaded_field_refuses_unknown_pk():
    a = AccountFactory()

    form = PreloadedForm(data={"account": a.pk})
    form.fields["account"].preload([])

    assert not form.is_valid()
    assert "account" in form.errors


def test_preloaded_field_returns_instance_for_known_pk_zero_queries(
    django_assert_num_queries,
):
    a = AccountFactory()

    form = PreloadedForm(data={"account": a.pk})
    form.fields["account"].preload([a])

    with django_assert_num_queries(0):
        assert form.is_valid(), form.errors

    assert form.cleaned_data["account"] == a


def test_preloaded_field_renders_choices_zero_queries(django_assert_num_queries):
    a1 = AccountFactory(title="A1")
    a2 = AccountFactory(title="A2")

    form = PreloadedForm()
    form.fields["account"].preload([a1, a2])

    with django_assert_num_queries(0):
        rendered = str(form["account"])

    assert f'<option value="{a1.pk}">{a1}</option>' in rendered
    assert f'<option value="{a2.pk}">{a2}</option>' in rendered


def test_preloaded_field_blank_first():
    a = AccountFactory()

    form = PreloadedForm()
    form.fields["account"].preload([a])

    rendered = str(form["account"])
    blank_index = rendered.index('<option value="" selected>')
    account_index = rendered.index(f'<option value="{a.pk}">')

    assert blank_index < account_index


def test_preloaded_field_default_before_preload_refuses_every_pk():
    a = AccountFactory()

    form = PreloadedForm(data={"account": a.pk})

    assert not form.is_valid()
    assert "account" in form.errors


def test_preloaded_field_counts_the_blank_among_its_choices():
    a = AccountFactory()

    field = PreloadedForm().fields["account"]
    field.preload([a])

    assert len(field.choices) == 2
    assert bool(field.choices)


def test_preloaded_field_without_blank_or_objects_has_no_choices():
    field = PreloadedModelChoiceField(queryset=Account.objects.none(), empty_label=None)

    assert len(field.choices) == 0
    assert not field.choices


def test_preloaded_field_default_before_preload_offers_only_blank():
    form = PreloadedForm()

    rendered = str(form["account"])

    assert rendered.count("<option") == 1
    assert '<option value="" selected>' in rendered
