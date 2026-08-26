import pytest
from django import forms

from ...lib.form_fields import CommaFloatField
from ...lib.form_widgets import DecimalCommaWidget


class Form(forms.Form):
    price = CommaFloatField()


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
